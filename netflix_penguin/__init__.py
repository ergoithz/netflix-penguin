
import re

from . import __meta__ as meta
from . import resources
from .layout import BrowserLayout
from .collections import AttrDefaultDict
from .gi import Gtk, Gio, Gdk, WebKit2


class Application(Gtk.Application):
    re_pipelight_so = re.compile(r'.*/libpipelight-silverlight[^/]+\.so$')
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
            cookie_storage_path=resources.cookie_storage
            )
        self.pressed_keys = set()
        self.fullscreen = False
        self.layout.connect({
            'window.window-state-event': self.on_window_state,
            'window.key-press-event': self.on_window_key_press,
            'window.key-release-event': self.on_window_key_release,
            'webview.create': self.on_create_request,
            'webview.decide-policy': self.on_decide_policy,
            'webview.load-changed': self.on_load_change
            })

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
            layout.popup.set_property('application', self)
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

    def on_plugins(self, source, res):
        pipelight = [
            plugin
            for plugin in source.get_plugins_finish(res)
            if self.re_pipelight_so.match(plugin.get_path())
            ]
        if not pipelight:
            self.layout.nosilverlight_info.set_property('visible', True)

    def on_load_change(self, webview, event):
        if event == WebKit2.LoadEvent.STARTED:
            self.layout.reload_button.set_property('sensitive', False)
            self.layout.hover_reload_button.set_property('sensitive', False)
        elif event == WebKit2.LoadEvent.COMMITTED:
            cgb = self.layout.webview.can_go_back()
            self.layout.back_button.set_property('sensitive', cgb)
            self.layout.hover_back_button.set_property('sensitive', cgb)
            cgf = self.layout.webview.can_go_forward()
            self.layout.forw_button.set_property('sensitive', cgf)
            self.layout.hover_forw_button.set_property('sensitive', cgf)
        elif event == WebKit2.LoadEvent.REDIRECTED:
            pass
        elif event == WebKit2.LoadEvent.FINISHED:
            self.layout.reload_button.set_property('sensitive', True)
            self.layout.hover_reload_button.set_property('sensitive', True)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        # NOTE: super(Application, self).do_startup()  # segfaults

        # action = Gio.SimpleAction.new('about', None)
        # action.connect('activate', self.on_about)
        # self.add_action(action)

        # action = Gio.SimpleAction.new('quit', None)
        # action.connect('activate', self.on_quit)
        # self.add_action(action)

        # builder = Gtk.Builder.new_from_string(MENU_XML, -1)
        # self.set_app_menu(self.layout.get_object('AppMenu'))

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
