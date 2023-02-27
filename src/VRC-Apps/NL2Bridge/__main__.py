import argparse
import asyncio
import math
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
    level=logging.INFO,
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
from scipy.spatial.transform import Rotation

def wrap_angle(angle):
    while angle > 360:
        angle -= 720 # Wrap to -360
    while angle < -360:
        angle += 720 # Wrap to +360
    return angle

savedrotations = [[0,0]]

class App:
    ws: pyWSConsole.Client

    #Intended to have lists appended to represent rotations for each frame
    #Uses an [roll, pitch] while the index of the list is the frame
    #First frame is 1 not 0, if you look up the rotation for frame zero (before first frame update) you should get no rotation
    global savedrotations

    def saveRotationsLoop(self, nl2: NoLimits2):
        record_number = 0
        get_telemetry = nl2telemetry.message.request.GetTelemetryMessage()
        roll_prev = 0
        roll_offset = 0
        pitch_prev = 0
        pitch_offset = 0
        while True:
            timeLoopStart = time.time()
            saved_frame = 1
            get_telemetry.set_request_id(record_number)
            nl2.send(get_telemetry)
            data = Answer.get_data(nl2.receive())

            if isinstance(data, ErrorData):
                raise Exception(data)

            record_number += 1

            if not data.in_play_mode:
                continue

            rotation: Rotation = Rotation.from_quat([
                data.rotation_quaternion_x,
                data.rotation_quaternion_y,
                data.rotation_quaternion_z,
                data.rotation_quaternion_w
            ])

            # Rotations are intrinsic. Remove yaw first.
            _, roll, pitch = rotation.as_euler('YZX', degrees=True)

            # Quaternion conversion limits angles between -180 to 180.
            # Firstly, we make this angle continuous by removing modulation.
            
            # Angle overflow
            if (roll < -90) and (roll_prev > 90):
                roll_offset += 360
            # Angle underflow
            elif (roll > 90) and (roll_prev < -90):
                roll_offset -= 360

            # Angle overflow
            if (pitch < -90) and (pitch_prev > 90):
                pitch_offset += 360
            # Angle underflow
            elif (pitch > 90) and (pitch_prev < -90):
                pitch_offset -= 360

            # We set the previous angles before we modify them with the offset.

            roll_prev = roll
            pitch_prev = pitch

            # Now, we take this continuous angle and limit it between -360 to 360
            # since this is what the Motion Client wants.

            roll = int(wrap_angle(roll + roll_offset))
            pitch = int(wrap_angle(pitch + pitch_offset))



            with suppress(Exception):
                #Adds the calculated roll and pitch to the savedrotations list, to be looked at later
                savedrotations.insert(saved_frame, [-roll, pitch])

            # To get consistent loop timing, we need to consider how long the loop itself takes.
            # The better solution to this is to use async/multithreading... maybe one day 
            timeLoopEnd = time.time()
            saved_frame += 1
            timeLoop = timeLoopEnd - timeLoopStart
            timeLoopTarget = 1000.0 / args.refreshrate
            sleepTime = max(0, timeLoopTarget - timeLoop) / 1000.0
            time.sleep(sleepTime)

    def loop(self, nl2: NoLimits2):
        while True:
            timeLoopStart = time.time()
            saved_frame = 1

            with suppress(Exception):
                self.ws.send(f"r,{savedrotations[saved_frame[0]]}") # r is an alias for setRollTarget
                self.ws.send(f"p,{savedrotations[saved_frame[1]]}") # p is an alias for setPitchTarget

            # To get consistent loop timing, we need to consider how long the loop itself takes.
            # The better solution to this is to use async/multithreading... maybe one day 
            timeLoopEnd = time.time()
            saved_frame += 1
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
                    self.saveRotationsLoop(nl2)
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
