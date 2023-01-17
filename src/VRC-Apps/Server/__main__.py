import asyncio
import os

from pyMaxFlight.Interface import MotionClient
from pyWSConsole import Server
from GUI import GUI

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

async def main():
    global ws
    mc = MotionClient()
    ws = Server()
    ws.register(
        mc.setRollTarget,
        mc.setPitchTarget,
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
        mc.getLogRange
    )
    ws.start()
    gui = GUI(
        ws,
        "VRC WebSockets Server",
        os.path.join(os.path.dirname(__file__), "icon.png")
    )
    await ws.task

if __name__=="__main__":
    asyncio.run(main())