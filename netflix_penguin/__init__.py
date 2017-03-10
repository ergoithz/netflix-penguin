
import re
import os
import os.path
import collections
import appdirs

from . import __meta__ as meta

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, Gdk, Gio, WebKit2, GObject  # noqa


class AttrDefaultDict(collections.defaultdict):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


class Layout(AttrDefaultDict):
    def __init__(self, path):
        self.builder = Gtk.Builder.new_from_file(path)
        super(Layout, self).__init__()

    def connect_signals(self, signals):
        self.builder.connect_signals(signals)

    def __missing__(self, key):
        return self.builder.get_object(key)


class Application(Gtk.Application):
    last_valid_uri = None
    appid = 'org.%s.%s' % (meta.__org__, meta.__app__)
    dirs = appdirs.AppDirs(meta.__app__, meta.__org__, meta.__version__)
    re_pipelight_so = re.compile(r'.*/libpipelight-silverlight[^/]+\.so$')
    re_accepted_uri = re.compile(
        r'^https?://www.netflix.com/('
        r'([a-z]{2}/)?([Ll]og|[Ss]ign)([Ii]n|[Oo]ut)|'
        r'browse|watch|[Kk]ids|([Mm]anage)?[Pp]rofiles([Gg]ate)?'
        r')(|\?.*|/.*)$'
        )
    userAgent = (
        'Mozilla/5.0 (Windows NT 6.3; rv:36.0) '
        'Gecko/20100101 Firefox/36.04'
        )
    platform = "Win32"
    script = '''
        (() => {
            const navigator = window.navigator;
            let modifiedNavigator;
            if ('userAgent' in Navigator.prototype) {
                // Chrome 43+
                modifiedNavigator = Navigator.prototype;
            } else {
                // Chrome 42-
                modifiedNavigator = Object.create(navigator);
                Object.defineProperty(window, 'navigator', {
                    value: modifiedNavigator,
                    configurable: false,
                    enumerable: false,
                    writable: false
                });
            }
            Object.defineProperties(modifiedNavigator, {
                userAgent: {
                    value: '%(userAgent)s',
                    configurable: false,
                    enumerable: true,
                    writable: false
                },
                appVersion: {
                    value: '%(appVersion)s',
                    configurable: false,
                    enumerable: true,
                    writable: false
                },
                platform: {
                    value: '%(platform)s',
                    configurable: false,
                    enumerable: true,
                    writable: false
                },
            });
        })();
        ''' % {
            'userAgent': userAgent,
            'appVersion': userAgent.split('/', 1)[1],
            'platform': platform
        }

    @classmethod
    def connect(cls, widget, *args, **kwargs):
        signals = dict(*args, **kwargs)
        if hasattr(widget, 'connect_signals'):
            return widget.connect_signals(signals)
        for name, callback in signals.items():
            widget.connect(name, callback)
        return signals

    def init_config(self):
        if not os.path.isdir(self.dirs.user_cache_dir):
            os.makedirs(self.dirs.user_cache_dir)

    def init_webview(self):
        manager = WebKit2.UserContentManager()
        manager.add_script(WebKit2.UserScript(
            self.script,
            WebKit2.UserContentInjectedFrames.ALL_FRAMES,
            WebKit2.UserScriptInjectionTime.START
        ))
        webview = WebKit2.WebView.new_with_user_content_manager(manager)
        context = webview.get_context()
        context.get_plugins(None, self.on_plugins)
        cookies = context.get_cookie_manager()
        cookies.set_persistent_storage(
            os.path.join(self.dirs.user_cache_dir, 'storage'),
            WebKit2.CookiePersistentStorage.SQLITE
            )
        settings = webview.get_settings()
        settings.set_user_agent(self.userAgent)
        settings.set_enable_java(False)
        settings.set_enable_plugins(True)
        settings.set_enable_fullscreen(True)
        settings.set_enable_page_cache(True)
        webview.set_settings(settings)
        webview.set_property('visible', True)
        self.connect(webview, {
            'load-changed': self.on_load_change,
            'notify::title': self.on_title_change
            })
        self.layout.hover_eventbox
        self.layout.webview = webview
        self.layout.main.pack_start(webview, True, True, 0)

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(
            *args,
            application_id=self.appid,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
            )
        self.options = AttrDefaultDict(lambda: None)
        self.layout = Layout(os.path.join(meta.__basedir__, 'layout.glade'))
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
        self.init_config()
        self.init_webview()

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
            uri = webview.get_uri()
            if (
              not self.options.unrestricted and
              not self.re_accepted_uri.match(uri)
              ):
                webview.stop_loading()
                Gtk.show_uri_on_window(
                    self.layout.window, uri, Gdk.CURRENT_TIME)
                return
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

    def do_startup(self):
        Gtk.Application.do_startup(self)
        # NOTE: super(Application, self).do_startup() segfaults

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
