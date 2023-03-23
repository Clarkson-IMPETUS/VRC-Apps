import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--keepmcopen",
    action='store',
    type=bool,
    default=True,
    const=True,
    nargs="?",
    help="Reopen the Motion Client if it is closed."
)

args = parser.parse_args()

# =============================================================================

import asyncio
import ctypes
import enum
import logging
import os
import threading

from pyMaxFlight import MotionClient
from pyWSConsole import Server
from .GUI import GUI

# =============================================================================

class MboxButtons(enum.IntEnum):
    MB_ABORTRETRYIGNORE = 0x00000002
    MB_CANCELTRYCONTINUE = 0x00000006
    MB_HELP = 0x00004000
    MB_OK = 0x00000000
    MB_OKCANCEL = 0x00000001
    MB_RETRYCANCEL = 0x00000005
    MB_YESNO = 0x00000004
    MB_YESNOCANCEL = 0x00000003

class MboxIcon(enum.IntEnum):
    MB_ICONEXCLAMATION = 0x00000030
    MB_ICONWARNING = 0x00000030
    MB_ICONINFORMATION = 0x00000040
    MB_ICONASTERISK = 0x00000040
    MB_ICONQUESTION = 0x00000020
    MB_ICONSTOP = 0x00000010
    MB_ICONERROR = 0x00000010
    MB_ICONHAND = 0x00000010

class MboxDefaultButton(enum.IntEnum):
    MB_DEFBUTTON1 = 0x00000000
    MB_DEFBUTTON2 = 0x00000100
    MB_DEFBUTTON3 = 0x00000200
    MB_DEFBUTTON4 = 0x00000300

class MboxModality(enum.IntEnum):
    MB_APPLMODAL = 0x00000000
    MB_SYSTEMMODAL = 0x00001000
    MB_TASKMODAL = 0x00002000

class MboxOther(enum.IntEnum):
    MB_DEFAULT_DESKTOP_ONLY = 0x00020000
    MB_RIGHT = 0x00080000
    MB_RTLREADING = 0x00100000
    MB_SETFOREGROUND = 0x00010000
    MB_TOPMOST = 0x00040000
    MB_SERVICE_NOTIFICATION = 0x00200000

def Mbox(
        title, text,
        buttons: MboxButtons = MboxButtons.MB_OK,
        default_button: MboxDefaultButton = MboxDefaultButton.MB_DEFBUTTON1,
        icon: MboxIcon = MboxIcon.MB_ICONINFORMATION,
        modality: MboxModality = MboxModality.MB_SYSTEMMODAL,
        other: MboxOther = 0
    ):
    style = int(buttons) | int(default_button) | int(icon) | int(modality) | int(other)
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

def RunFuncInThread(func, *args, **kwargs):
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.start()
    return thread

# =============================================================================

class App:
    running = True
    gui: GUI
    mc: MotionClient
    ws: Server

    async def loop(self):
        if not args.keepmcopen:
            return

        while self.running:
            if not self.mc.isProcessOpen:
                warning_msg = "Please keep the Motion Client open. Closing it will reload it automatically."
                logging.warn(warning_msg)

                # Run this in a background thread else it will block the server
                RunFuncInThread(
                    Mbox,
                    "VRC-Apps.Server Message",
                    warning_msg,
                    icon=MboxIcon.MB_ICONEXCLAMATION,
                    other=MboxOther.MB_SETFOREGROUND | MboxOther.MB_TOPMOST
                )

                # Run motion client and continue
                path_motionclient = "C:\\Program Files\\MaxFlight\\Motion Platform\\MFMotionClient.exe"
                os.startfile(path_motionclient)

            await asyncio.sleep(5)

    def initLogging(self):
        logFormat = '%(asctime)s %(levelname)-8s %(message)s'
        dateFormat = '%Y-%m-%d %H:%M:%S'
        logging.basicConfig(
            encoding="utf-8",
            level=logging.INFO,
            format=logFormat,
            datefmt=dateFormat
        )

    async def main(self):
        self.initLogging()

        self.mc = MotionClient()
        self.ws = Server()
        
        # We have to convert to float first because we're coming from a string.
        # For example, int("1.0") will not work, but int(float("1.0")) will.
        setRollTargetWrapped = lambda x: self.mc.setRollTarget(int(float(x)))
        setPitchTargetWrapped = lambda x: self.mc.setPitchTarget(int(float(x)))
        self.ws.register(
            self.mc.liftRaise,
            self.mc.liftStop,
            self.mc.liftLower,
            self.mc.start,
            self.mc.run,
            self.mc.freeze,
            self.mc.stop,
            self.mc.forceRaised,
            self.mc.counterweightFwd,
            self.mc.counterweightBwd,
            self.mc.home,
            self.mc.status,
            s=self.mc.status, # alias
            r=setRollTargetWrapped, # Alias 
            p=setPitchTargetWrapped, # Alias 
            setRollTarget=setRollTargetWrapped,
            setPitchTarget=setPitchTargetWrapped
        )
        self.ws.start()
        
        self.gui = GUI(
            self.ws,
            "VRC WebSockets Server",
            os.path.join(os.path.dirname(__file__), "icon.png")
        )

        asyncio.create_task(self.loop())
        await self.ws.task
        self.running = False

    def __del__(self):
        self.running = False
        self.gui.trayIcon.stop()

    def __init__(self):
        asyncio.run(self.main())
        

# =============================================================================

if __name__=="__main__":
    app = App()