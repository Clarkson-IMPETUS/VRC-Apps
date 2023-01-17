PORT_LIGHT = "COM5"
REFRESH_RATE = 30.0 # hz
SERVER_ADDR = "192.168.1.99"
AUTO_OFF_TIME = 5 * 60
AUTO_OFF_THRESH = 0.1

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
        rollMoved = abs(rollReal - self.rollPrev) > AUTO_OFF_THRESH
        pitchMoved = abs(pitchReal - self.pitchPrev) > AUTO_OFF_THRESH
        if rollMoved or pitchMoved:
            self.rollPrev = rollReal
            self.pitchPrev = pitchReal
            self.idleTimestamp = time.time()
        elif (time.time() - self.idleTimestamp) > AUTO_OFF_TIME:
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
            with suppress(Exception): self.ws.send("status")
            await asyncio.sleep(1.0 / REFRESH_RATE)

    async def main(self):
        # Secondary async task allows ws task to run interrupted
        self.ws.start()
        asyncio.create_task(self.loop())
        await self.ws.task

    def __init__(self):
        self.ser = serial.Serial(PORT_LIGHT)
        self.ws = Client(SERVER_ADDR)
        self.ws.register(status=self.statusHandler)

        self.gui = GUI(
            self.ws,
            "VRC WebSockets Client",
            os.path.join(os.path.dirname(__file__), "icon.png")
        )

        asyncio.run(self.main())

if __name__=="__main__":
    app = App()