
import re
import os.path
import collections

from . import __meta__ as meta

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, Gdk, Gio, WebKit2 # noqa


class Layout(collections.defaultdict):
    def __init__(self, path, signal_handlers):
        self.builder = Gtk.Builder.new_from_file(path)
        self.builder.connect_signals(signal_handlers)
        super(Layout, self).__init__()

    def __missing__(self, key):
        return self.builder.get_object(key)

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


class Application(Gtk.Application):
    re_pipelight_so = re.compile(r'.*/libpipelight-silverlight[^/]+\.so$')
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
        settings = webview.get_settings()
        settings.set_user_agent(self.userAgent)
        webview.set_settings(settings)
        webview.set_property('visible', True)
        webview.connect('load-changed', self.on_load_change)
        webview.connect('notify::title', self.on_title_change)

        self.layout.hover_eventbox
        self.layout.webview = webview
        self.layout.main.pack_start(webview, True, True, 0)

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(
            *args,
            application_id="org.example.myapp",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
            )
        signal_handlers = {
            'back_button_click': lambda b: self.layout.webview.go_back(),
            'forw_button_click': lambda b: self.layout.webview.go_forward(),
            'reload_button_click': lambda b: self.layout.webview.reload(),
            'fullscreen_button_click': self.on_toggle_fullscreen,
            'hover_headerbar_leave': self.on_hover_headerbar_leave,
            'window_state': self.on_window_state,
            'window_key_release': self.on_window_key,
        }
        self.layout = Layout(
            os.path.join(meta.__basedir__, 'layout.glade'),
            signal_handlers
            )
        self.init_webview()

    def on_toggle_fullscreen(self, source):
        if self.fullscreen:
            self.layout.window.unfullscreen()
        else:
            self.layout.window.fullscreen()
        self.layout.hover_headerbar.set_property('visible', False)

    def on_window_state(self, source, event):
        self.fullscreen = Gdk.WindowState.FULLSCREEN & event.new_window_state

        if self.fullscreen:
            # TODO: fullscreen message
            pass

    def on_window_key(self, source, event):
        if self.fullscreen:
            if event.keyval == Gdk.KEY_Escape:
                self.layout.window.unfullscreen()
            elif event.keyval == Gdk.KEY_Alt_L:
                value = self.layout.hover_headerbar.get_property('visible')
                self.layout.hover_headerbar.set_property('visible', not value)

    def on_hover_headerbar_leave(self):
        self.layout.hover_headerbar.set_property('visible', False)

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
        # options = command_line.get_options_dict()
        # if options.contains('test'):
        #    print('Test argument recieved')

        self.activate()
        return 0

    def on_quit(self, action, param):
        self.quit()
