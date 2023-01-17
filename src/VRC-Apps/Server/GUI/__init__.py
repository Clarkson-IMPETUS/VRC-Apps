import sys
import logging
import os

from pyWSConsole import Server

from contextlib import contextmanager
@contextmanager
def warnOnExcept(warningMsg: str = ""):
    try:
        yield
    except Exception as e:
        logging.warning(f"{warningMsg} ({e})")

with warnOnExcept("There will be no tray indicator."):
    import pystray
    from PIL import Image

with warnOnExcept("Copying the URI from the tray menu will not work."):
    import pyperclip

def restart(*args, **kawrgs):
    os.execv(sys.executable, [os.path.basename(sys.executable)] + sys.argv)

class GUI:
    ws: Server = None
    trayIcon: pystray.Icon = None

    def copyURI(self, *args):
        if "pyperclip" not in sys.modules: return
        pyperclip.copy(self.ws.getURI())

    def menu(self):
        yield pystray.MenuItem(
            self._title,
            None,
            enabled=False
        )
        yield pystray.Menu.SEPARATOR
        yield pystray.MenuItem(
            "Listening on:",
            None,
            enabled=False
        )
        yield pystray.MenuItem(
            self.ws.getURI(),
            self.copyURI
        )
        yield pystray.Menu.SEPARATOR
        yield pystray.MenuItem(
            'Restart Server',
            restart
        )

    def __init__(self, ws, title="WebSockets Server", iconPath=None):
        self.ws = ws
        self._title = title

        if "pystray" not in sys.modules: return
        if "PIL.Image" not in sys.modules: return

        self.trayIcon = pystray.Icon(
            title,
            Image.open(iconPath),
            menu=pystray.Menu(self.menu)
        )

        self.trayIcon.run_detached()    