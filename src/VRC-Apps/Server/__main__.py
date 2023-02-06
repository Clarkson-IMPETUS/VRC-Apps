import asyncio
import os
from contextlib import suppress

from pyMaxFlight.Interface import MotionClient
from pyWSConsole import Server
from .GUI import GUI

import logging
logFormat = '%(asctime)s %(levelname)-8s %(message)s'
dateFormat = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(
    encoding="utf-8",
    level=logging.INFO,
    format=logFormat,
    datefmt=dateFormat
)

ws: Server = None
gui = None

async def main():
    global gui
    global ws
    mc = MotionClient()
    ws = Server()
    setRollTargetWrapped = lambda x: mc.setRollTarget(int(float(x)))
    setPitchTargetWrapped = lambda x: mc.setPitchTarget(int(float(x)))
    ws.register(
        setRollTargetWrapped,
        setPitchTargetWrapped,
        mc.liftRaise,
        mc.liftStop,
        mc.liftLower,
        mc.start,
        mc.run,
        mc.freeze,
        mc.stop,
        mc.forceRaised,
        mc.counterweightFwd,
        mc.counterweightBwd,
        mc.home,
        mc.status,
        # mc.getLogRange
        r=setRollTargetWrapped, # Alias 
        p=setPitchTargetWrapped, # Alias 
    )
    ws.start()
    gui = GUI(
        ws,
        "VRC WebSockets Server",
        os.path.join(os.path.dirname(__file__), "icon.png")
    )
    await ws.task

if __name__=="__main__":
    with suppress(Exception): asyncio.run(main())
    gui.trayIcon.stop()
