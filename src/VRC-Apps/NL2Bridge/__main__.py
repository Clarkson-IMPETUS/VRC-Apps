import argparse

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

import asyncio
from contextlib import suppress
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

try:
    from scipy.spatial.transform import Rotation
except ImportError:
    raise ImportError("Please install scipy: pip install scipy")

def wrap_angle(angle):
    while angle > 360:
        angle -= 720 # Wrap to -360
    while angle < -360:
        angle += 720 # Wrap to +360
    return angle

class OrientationProvider:
    _active = False
    _roll = 0
    _pitch = 0

    def update(self):
        pass

    @property
    def roll(self):
        return self._roll if self._active else 0

    @property
    def pitch(self):
        return self._pitch if self._active else 0

    @property
    def active(self):
        return self._active

class NL2OrientationProvider(OrientationProvider):
    _get_telemetry = nl2telemetry.message.request.GetTelemetryMessage()
    _record_number = 0
    _roll_prev = 0
    _roll_offset = 0
    _pitch_prev = 0
    _pitch_offset = 0

    def __init__(self):
        self._nl2 = NoLimits2(args.nl2address, args.nl2port)
        logging.info("NL2 connection successful!")

    def update(self):
        self._get_telemetry.set_request_id(self._record_number)
        self._nl2.send(self._get_telemetry)
        data = Answer.get_data(self._nl2.receive())

        if isinstance(data, ErrorData):
            raise Exception(data)

        self._record_number += 1

        if not data.in_play_mode:
            self._roll = 0
            self._pitch = 0
            self._active = False
            return

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
        if (roll < -90) and (self._roll_prev > 90):
            self._roll_offset += 360
        # Angle underflow
        elif (roll > 90) and (self._roll_prev < -90):
            self._roll_offset -= 360

        # Angle overflow
        if (pitch < -90) and (self._pitch_prev > 90):
            self._pitch_offset += 360
        # Angle underflow
        elif (pitch > 90) and (self._pitch_prev < -90):
            self._pitch_offset -= 360

        # We set the previous angles before we modify them with the offset.
        self._roll_prev = roll
        self._pitch_prev = pitch

        # Now, we take this continuous angle and limit it between -360 to 360
        # since this is what the Motion Client wants.

        self._roll = int(wrap_angle(roll + self._roll_offset))
        self._pitch = int(wrap_angle(pitch + self._pitch_offset))
        self._active = True

    def __del__(self):
        self._nl2.close()

class App:
    ws: pyWSConsole.Client

    def loop(self):
        orientation_provider = NL2OrientationProvider()

        while True:
            time_loop_start = time.time()
            
            active_prev = orientation_provider.active
            orientation_provider.update()
            if orientation_provider.active or active_prev:
                with suppress(Exception):
                    self.ws.send("r", str(-orientation_provider.roll)) # r is an alias for setRollTarget
                    self.ws.send("p", str(orientation_provider.pitch)) # p is an alias for setPitchTarget

            # To get consistent loop timing, we need to consider how long the loop itself takes.
            # The better solution to this is to use async/multithreading... maybe one day 
            time_loop_end = time.time()
            time_loop = time_loop_end - time_loop_start
            time_loop_target = 1000.0 / args.refreshrate
            sleep_time = max(0, time_loop_target - time_loop) / 1000.0
            time.sleep(sleep_time)

    async def main(self):
        self.ws = pyWSConsole.Client(args.wsaddress, port=args.wsport)
        self.ws.start()

        while True:
            try:
                self.loop()
            except Exception as e:
                logging.exception(e)
                logging.debug(f"Attempting reconnection in {args.retryinterval} seconds")
                time.sleep(args.retryinterval)
            except KeyboardInterrupt as e:
                break # Allows exit via Ctrl-C

    def __init__(self):
        asyncio.run(self.main())

if __name__ == '__main__':
    app = App()
