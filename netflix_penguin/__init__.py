
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
    re_frame_uri = re.compile(r'^https?://[^.]+\.facebook\.com/.*$')

    @classmethod
    def connect(cls, widget, *args, **kwargs):
        signals = dict(*args, **kwargs)
        if hasattr(widget, 'connect_signals'):
            return widget.connect_signals(signals)
        for name, callback in signals.items():
            widget.connect(name, callback)
        return signals

    def init_config(self):
        pass

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
        self.connect(self.layout, {
            'back_button_click': lambda b: self.layout.webview.go_back(),
            'forw_button_click': lambda b: self.layout.webview.go_forward(),
            'reload_button_click': lambda b: self.layout.webview.reload(),
            'fullscreen_button_click': self.on_fullscreen,
            'unfullscreen_button_click': self.on_unfullscreen,
            'window_state': self.on_window_state,
            'window_key_press': self.on_window_key_press,
            'window_key_release': self.on_window_key_release,
            })
        self.connect(self.layout.webview, {
            'decide-policy': self.on_decide_policy,
            'load-changed': self.on_load_change,
            'notify::title': self.on_title_change
            })
        self.init_config()

    def on_fullscreen(self, source):
        self.layout.window.fullscreen()

    def on_unfullscreen(self, source):
        self.layout.window.unfullscreen()

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
              self.re_frame_uri.match(uri) and
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

    def on_new_window(self, decision):
        # frame = decision.get_frame_name()
        action = decision.get_navigation_action()
        # navtype = action.get_navigation_type()
        request = action.get_request()
        uri = request.get_uri()
        # method = request.get_http_method()
        # headers= request.get_http_headers()
        if self.re_login_urls.match(uri):
            self.do_open_window(uri)
        else:
            Gtk.show_uri_on_window(
                self.layout.window,
                uri,
                Gdk.CURRENT_TIME
                )
        decision.ignore()
        return True

    def on_response(self, decision):
        return

    def on_decide_policy(self, webview, decision, type):
        if type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            return self.on_navigation(decision)
        if type == WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION:
            return self.on_new_window(decision)
        if type == WebKit2.PolicyDecisionType.RESPONSE:
            return self.on_response(decision)

    def on_window_key_press(self, source, event):
        if event.keyval in self.pressed_keys:
            return
        self.pressed_keys.add(event.keyval)
        if self.fullscreen:
            if event.keyval in (Gdk.KEY_Escape, Gdk.KEY_F11):
                self.layout.window.unfullscreen()
            elif event.keyval == Gdk.KEY_Alt_L:
                value = self.layout.hover_revealer.get_reveal_child()
                self.layout.hover_revealer.set_reveal_child(not value)
        elif event.keyval == Gdk.KEY_F11:
            self.layout.window.fullscreen()

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

    def on_title_change(self, webview, param):
        title = webview.get_title()
        title = None if title == self.layout.headerbar.get_title() else title
        self.layout.headerbar.set_subtitle(title)
        self.layout.hover_headerbar.set_subtitle(title)

    def do_open_window(self, uri):
        layout = self.layout.copy()
        layout.clear()
        layout.popup.show()

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
        self.layout.window.set_application(self)
        self.layout.window.present()
        self.layout.webview.load_uri('http://www.netflix.com/browse')

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        self.options.unrestricted = options.contains('--unrestricted')
        self.activate()
        return 0

    def on_quit(self, action, param):
        self.quit()
