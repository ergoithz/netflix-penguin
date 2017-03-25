
from .collections import AttrDefaultDict
from .gi import Gtk, WebKit2


class Layout(AttrDefaultDict):
    def __init__(self, path):
        self.path = path
        self.builder = Gtk.Builder.new_from_file(path)
        super(Layout, self).__init__()

    def connect(self, signals):
        for spec, handler in signals.items():
            widget, signal = spec.split('.', 1)
            self[widget].connect(signal, handler)

    def __missing__(self, key):
        return self.builder.get_object(key)


class PopUpLayout(Layout):
    def __init__(self, path, parent):
        super(PopUpLayout, self).__init__(path)

        self.popup.set_properties({
            'visible': True,
            })
        self.popup.set_transient_for(parent.get_toplevel())

        webview = WebKit2.WebView.new_with_related_view(parent)

        self.webview = webview
        self.popup.add(webview)
        self.connect({
            'popup_back_button.clicked': lambda b: self.webview.go_back(),
            'popup_forw_button.clicked': lambda b: self.webview.go_forward(),
            'popup_reload_button.clicked': lambda b: self.webview.reload(),
            'webview.ready-to-show': lambda source: source.show(),
            'webview.load-changed': self.on_load_change,
            'webview.notify::title': self.on_title_change,
            'webview.notify::uri': self.on_uri_change,
            'webview.close': lambda source: self.popup.destroy(),
            })

    def on_title_change(self, webview, param):
        title = webview.get_title()
        self.popup_header.set_title(title)

    def on_uri_change(self, webview, param):
        uri = webview.get_uri()
        self.popup_header.set_subtitle(uri)

    def on_load_change(self, webview, event):
        if event == WebKit2.LoadEvent.STARTED:
            self.popup_reload_button.set_property('sensitive', False)
        elif event == WebKit2.LoadEvent.COMMITTED:
            cgb = self.webview.can_go_back()
            self.popup_back_button.set_property('sensitive', cgb)
            cgf = self.webview.can_go_forward()
            self.popup_forw_button.set_property('sensitive', cgf)
        elif event == WebKit2.LoadEvent.REDIRECTED:
            pass
        elif event == WebKit2.LoadEvent.FINISHED:
            self.popup_reload_button.set_property('sensitive', True)


class BrowserLayout(Layout):
    popup_layout_class = PopUpLayout
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

    def __init__(self, path, cookie_storage_path):
        super(BrowserLayout, self).__init__(path)

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
            cookie_storage_path,
            WebKit2.CookiePersistentStorage.SQLITE
            )
        settings = webview.get_settings()
        settings.set_properties({
            'user-agent': self.userAgent,
            'enable-java': False,
            'enable-plugins': True,
            'enable-fullscreen': True,
            'enable-page-cache': True,
            })
        webview.set_settings(settings)
        webview.show()
        self.webview = webview
        self.main.pack_start(webview, True, True, 0)
        w = self.window
        self.connect({
            'back_button.clicked': lambda b: webview.go_back(),
            'hover_back_button.clicked': lambda b: webview.go_back(),
            'forw_button.clicked': lambda b: webview.go_forward(),
            'hover_forw_button.clicked': lambda b: webview.go_forward(),
            'reload_button.clicked': lambda b: webview.reload(),
            'hover_reload_button.clicked': lambda b: webview.reload(),
            'fullscreen_button.clicked': lambda b: w.fullscreen(),
            'hover_unfullscreen_button.clicked': lambda b: w.unfullscreen(),
            'webview.notify::title': self.on_title_change,
            })

    def on_title_change(self, webview, param):
        title = webview.get_title()
        title = None if title == self.headerbar.get_title() else title
        self.headerbar.set_subtitle(title)
        self.hover_headerbar.set_subtitle(title)

    def create_popup(self):
        return self.popup_layout_class(self.path, self.webview)
