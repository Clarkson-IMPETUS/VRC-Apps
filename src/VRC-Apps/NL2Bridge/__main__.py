import argparse
import asyncio
from contextlib import suppress

parser = argparse.ArgumentParser()
parser.add_argument(
    "--refreshrate",
    default=30,
    type=float,
    help="Frequency at which status is requested from the server in hz."
)
parser.add_argument(
    "--retryinterval",
    default=5,
    type=float,
    help="Delay in seconds between attempts to reconnect to the NoLimits 2 server."
)
parser.add_argument(
    "--wsaddress",
    default="192.168.1.99",
    help="Address of WebSockets server."
)
parser.add_argument(
    "--wsport",
    default=8765,
    type=int,
    help="Port of WebSockets server."
)
parser.add_argument(
    "--nl2address",
    default="127.0.0.1",
    help="Address of the NoLimits 2 telemetry server."
)
parser.add_argument(
    "--nl2port",
    default=15151,
    type=int,
    help="Port of the NoLimits 2 telemetry server."
)

args = parser.parse_args()

import logging
logFormat = '%(asctime)s %(levelname)-8s %(message)s'
dateFormat = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(
    encoding="utf-8",
    level=logging.DEBUG,
    format=logFormat,
    datefmt=dateFormat
)

from nl2telemetry.message import Answer
from nl2telemetry.message.reply import ErrorData
import nl2telemetry.message.request
from nl2telemetry import NoLimits2
import pyWSConsole

import time
import math

class Quaternion:
    x: float
    y: float
    z: float
    w: float

    def set(self, x, y, z, w):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def pitch(self) -> float:
        vx = 2*(self.x*self.y + self.w*self.y) 
        vy = 2*(self.w*self.x - self.y*self.z)
        vz = 1.0 - 2*(self.x*self.x + self.y*self.y)
        
        return math.atan2(vy, math.sqrt(vx*vx + vz*vz))

    def yaw(self) -> float:
        return math.atan2(2*(self.x*self.y + self.w*self.y), 1.0 - 2*(self.x*self.x + self.y*self.y))

    def roll(self) -> float:
        return math.atan2(2*(self.x*self.y + self.w*self.z), 1.0 - 2*(self.x*self.x + self.z*self.z));

class App:
    ws: pyWSConsole.Client

    def loop(self, nl2: NoLimits2):
        record_number = 0
        get_telemetry = nl2telemetry.message.request.GetTelemetryMessage()
        quat = Quaternion()
        while True:
            timeLoopStart = time.time()
            get_telemetry.set_request_id(record_number)
            nl2.send(get_telemetry)
            data = Answer.get_data(nl2.receive())

            if isinstance(data, ErrorData):
                raise Exception(data)

            record_number += 1

            if not data.in_play_mode:
                continue

            quat.set(
                data.rotation_quaternion_x,
                data.rotation_quaternion_y,
                data.rotation_quaternion_z,
                data.rotation_quaternion_w
            )
            with suppress(Exception):
                self.ws.send(f"r,{quat.roll():.2f}") # r is an alias for setRollTarget
                self.ws.send(f"p,{quat.pitch():.2f}") # p is an alias for setPitchTarget

            # To get consistent loop timing, we need to consider how long the loop itself takes.
            # The better solution to this is to use async/multithreading... maybe one day 
            timeLoopEnd = time.time()
            timeLoop = timeLoopEnd - timeLoopStart
            timeLoopTarget = 1000.0 / args.refreshrate
            sleepTime = max(0, timeLoopTarget - timeLoop) / 1000.0
            time.sleep(sleepTime)

    async def main(self):
        self.ws.start()

        while True:
            try:
                with NoLimits2(args.nl2address, args.nl2port) as nl2:
                    logging.info("NL2 connection successful!")
                    self.loop(nl2)
            except Exception as e:
                logging.exception(e)
                logging.debug(f"Attempting reconnection in {args.retryinterval} seconds")
                time.sleep(args.retryinterval)
            except KeyboardInterrupt as e:
                break # Allows exit via Ctrl-C

    def __init__(self):
        self.ws = pyWSConsole.Client(args.wsaddress, port=args.wsport)
        asyncio.run(self.main())

if __name__ == '__main__':
    app = App()
