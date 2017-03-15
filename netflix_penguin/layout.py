
from .collections import AttrDefaultDict
from .gi import Gtk, WebKit2


class Layout(AttrDefaultDict):
    def __init__(self, path):
        self.path = path
        self.builder = Gtk.Builder.new_from_file(path)
        super(Layout, self).__init__()

    def connect_signals(self, signals):
        self.builder.connect_signals(signals)

    def __missing__(self, key):
        return self.builder.get_object(key)

    def create(self, key):
        obj = Gtk.Builder.new_from_file(self.path).get_object(key)
        if obj.get_parent():
            obj.unparent()
        return obj


class BrowserLayout(Layout):
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
        webview.set_property('visible', True)
        self.webview = webview
        self.main.pack_start(webview, True, True, 0)
