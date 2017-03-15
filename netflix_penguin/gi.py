
from __future__ import absolute_import

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, Gdk, Gio, WebKit2, GObject  # noqa

__all__ = (Gtk, Gdk, Gio, WebKit2, GObject)
