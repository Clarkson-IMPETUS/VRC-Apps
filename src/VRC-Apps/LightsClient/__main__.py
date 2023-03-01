import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "-s",
    "--serialport",
    default="COM5",
    help="Name or path of serial port for the Arduino light controller."
)
parser.add_argument(
    "-r",
    "--refreshrate",
    default=5,
    type=float,
    help="Frequency at which status is requested from the server in hz."
)
parser.add_argument(
    "-a",
    "--address",
    default="192.168.1.99",
    help="Address of WebSockets server."
)
parser.add_argument(
    "-p",
    "--port",
    default=8765,
    type=int,
    help="Port of WebSockets server."
)
parser.add_argument(
    "--autoofftime",
    default=5 * 60,
    type=float,
    help="""Time (in seconds) for cabin to remain idle before lights are automatically shut off."""
)
parser.add_argument(
    "--autooffthresh",
    default=0.1,
    type=float,
    help="Threshold of movement (in degrees) before idle timer is reset."
)

args = parser.parse_args()

import asyncio
from contextlib import suppress
import serial
import time
import os

from pyWSConsole import Client
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

class App:
    ws: Client = None
    idleTimestamp: int = 0
    rollPrev: float = 0
    pitchPrev: float = 0

    def statusHandler(self, status):
        lightOff = True

        isOpen = status["canopyOpen"]
        if isOpen:
            lightOff = False

        # If the machine is open but idle, turn off the lights
        rollReal = status["roll"]["real"]
        pitchReal = status["pitch"]["real"]
        rollMoved = abs(rollReal - self.rollPrev) > args.autooffthresh
        pitchMoved = abs(pitchReal - self.pitchPrev) > args.autooffthresh
        if rollMoved or pitchMoved:
            self.rollPrev = rollReal
            self.pitchPrev = pitchReal
            self.idleTimestamp = time.time()
        elif (time.time() - self.idleTimestamp) > args.autoofftime:
            lightOff = True

        # We want the lights ON in an emergency no matter how long the machine is idle
        eStop = status["emergencyStop"]
        if eStop:
            lightOff = False

        # Couldnt get arduino serial to accept a plain 1 or 0 dunno why
        lightOffStr = b'1' if lightOff else b'0'
        self.ser.write(lightOffStr)

    async def loop(self):
        while True:
            with suppress(Exception): self.ws.send("s") # "s" is an alias for "status"
            await asyncio.sleep(1.0 / args.refreshrate)

    async def main(self):
        # Secondary async task allows ws task to run interrupted
        self.ws.start()
        asyncio.create_task(self.loop())
        await self.ws.task

    def __init__(self):
        self.ser = serial.Serial(args.serialport)
        self.ws = Client(args.address)
        self.ws.register(status=self.statusHandler)

        self.gui = GUI(
            self.ws,
            "VRC WebSockets Client",
            os.path.join(os.path.dirname(__file__), "icon.png")
        )

        with suppress(Exception): asyncio.run(self.main())
        self.gui.trayIcon.stop()

if __name__=="__main__":
    app = App()