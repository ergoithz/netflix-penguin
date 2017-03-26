
import re

from . import __meta__ as meta
from . import resources
from .utils import human_size
from .layout import BrowserLayout, Layout
from .collections import AttrDefaultDict
from .gi import Gtk, Gio, Gdk, WebKit2


class Application(Gtk.Application):
    re_accepted_uri = re.compile(
        r'^https?://www\.netflix\.com/('
        r'([a-z]{2}/)?([Ll]og|[Ss]ign)([Ii]n|[Oo]ut)([Hh]elp)?|'
        r'browse|watch|title|[Kk]ids|([Mm]anage)?[Pp]rofiles([Gg]ate)?'
        r')(|(#|\?|/).*)$'
        )
    re_popup_uri = re.compile(r'^https?://[^.]+\.facebook\.com/.*$')
    home_uri = 'http://www.netflix.com/browse'

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(
            *args,
            application_id='org.{}.{}'.format(meta.__org__, meta.__app__),
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
            )
        self.options = AttrDefaultDict(lambda: None)
        self.layout = BrowserLayout(
            resources.layout,
            cookie_storage_path=resources.storage
            )
        self.menu = Layout(resources.menu)
        self.pressed_keys = set()
        self.fullscreen = False
        self.layout.connect({
            'window.window-state-event': self.on_window_state,
            'window.key-press-event': self.on_window_key_press,
            'window.key-release-event': self.on_window_key_release,
            'webview.create': self.on_create_request,
            'webview.decide-policy': self.on_decide_policy,
            'webview.load-changed': self.on_load_change,
            'about.delete-event': self.on_dialog_delete,
            'preferences.delete-event': self.on_dialog_delete,
            'about_close.clicked': self.on_dialog_close,
            'preferences_close.clicked': self.on_dialog_close,
            'clear_data.clicked': self.on_clear_data,
            })
        self.layout.set({
            'about.program-name': meta.__appname__,
            'about.version': meta.__version__,
            'about.authors': [meta.__author__],
            })

    def on_clear_data(self, widget):
        context = self.layout.webview.get_context()
        context.clear_cache()
        manager = context.get_cookie_manager()
        manager.delete_all_cookies()
        self.update_preferences_size()

    def on_dialog_close(self, widget):
        widget.get_toplevel().hide()

    def on_dialog_delete(self, source, param):
        source.hide()
        return True

    def on_window_state(self, source, event):
        fullscreen = Gdk.WindowState.FULLSCREEN & event.new_window_state
        if fullscreen != self.fullscreen:
            self.fullscreen = fullscreen
            self.layout.hover_revealer.set_property('visible', fullscreen)
            self.layout.hover_revealer.set_reveal_child(not fullscreen)

    def on_navigation(self, decision):
        action = decision.get_navigation_action()
        request = action.get_request()
        uri = request.get_uri()
        navtype = action.get_navigation_type()
        if (
          self.options.unrestricted or
          self.re_accepted_uri.match(uri) or (
              self.re_popup_uri.match(uri) and
              navtype == WebKit2.NavigationType.OTHER
              ) or
          navtype in (
              WebKit2.NavigationType.FORM_SUBMITTED,
              WebKit2.NavigationType.FORM_RESUBMITTED,
              WebKit2.NavigationType.RELOAD
              )):
            decision.use()
            return True
        if navtype == WebKit2.NavigationType.LINK_CLICKED:
            Gtk.show_uri_on_window(self.layout.window, uri, Gdk.CURRENT_TIME)
        decision.ignore()
        return True

    def on_create_request(self, webview, action):
        request = action.get_request()
        uri = request.get_uri()
        if self.re_popup_uri.match(uri):
            layout = self.layout.create_popup()
            layout.popup.set_application(self)
            layout.popup.show()
            return layout.webview

    def on_decide_policy(self, webview, decision, type):
        if type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            return self.on_navigation(decision)

    def on_window_key_press(self, source, event):
        if event.keyval in self.pressed_keys:
            return True
        self.pressed_keys.add(event.keyval)
        if self.fullscreen:
            if event.keyval in (Gdk.KEY_Escape, Gdk.KEY_F11):
                self.layout.window.unfullscreen()
                return True
            elif event.keyval == Gdk.KEY_Alt_L:
                value = self.layout.hover_revealer.get_reveal_child()
                self.layout.hover_revealer.set_reveal_child(not value)
                return True
        elif event.keyval == Gdk.KEY_F11:
            self.layout.window.fullscreen()
            return True
        return False

    def on_window_key_release(self, source, event):
        self.pressed_keys.discard(event.keyval)

    def on_load_change(self, webview, event):
        if event == WebKit2.LoadEvent.STARTED:
            self.layout.set({
                'reload_button.sensitive': False,
                'hover_reload_button.sensitive': False,
                })
        elif event == WebKit2.LoadEvent.COMMITTED:
            cgb = self.layout.webview.can_go_back()
            cgf = self.layout.webview.can_go_forward()
            self.layout.set({
                'back_button.sensitive': cgb,
                'hover_back_button.sensitive': cgb,
                'forw_button.sensitive': cgf,
                'hover_forw_button.sensitive': cgf,
                })
        elif event == WebKit2.LoadEvent.REDIRECTED:
            pass
        elif event == WebKit2.LoadEvent.FINISHED:
            self.layout.set({
                'reload_button.sensitive': True,
                'hover_reload_button.sensitive': True,
                })

    def on_about(self, source, param):
        self.layout.about.show()

    def on_preferences(self, source, param):
        self.update_preferences_size()
        self.layout.preferences.show()

    def update_preferences_size(self):
        size = resources.count_cache_size()
        self.layout.data_size_label.set_label(human_size(size))

    def do_startup(self):
        Gtk.Application.do_startup(self)
        # NOTE: super(Application, self).do_startup()  # segfaults

        action = Gio.SimpleAction.new('preferences', None)
        action.connect('activate', self.on_preferences)
        self.add_action(action)

        action = Gio.SimpleAction.new('about', None)
        action.connect('activate', self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', self.on_quit)
        self.add_action(action)

        self.set_app_menu(self.menu['menu'])

    def do_activate(self):
        resources.create_dirs()
        self.layout.window.set_application(self)
        self.layout.window.present()
        self.layout.webview.load_uri(self.home_uri)

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        self.options.unrestricted = options.contains('--unrestricted')
        self.activate()
        return 0

    def on_quit(self, action, param):
        self.quit()
