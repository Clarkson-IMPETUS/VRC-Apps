# VRC-Apps.LightsClient

Controls the retrofitted lights in the VRC.

## Usage
```console
python -m VRC-Apps.LightsClient -h
usage: __main__.py [-h] [-s SERIALPORT] [-r REFRESHRATE] [-a ADDRESS] [-p PORT] [--autoofftime AUTOOFFTIME]
                   [--autooffthresh AUTOOFFTHRESH]

optional arguments:
  -h, --help            show this help message and exit
  -s SERIALPORT, --serialport SERIALPORT
                        Name or path of serial port for the Arduino light controller.
  -r REFRESHRATE, --refreshrate REFRESHRATE
                        Frequency at which status is requested from the server in hz.
  -a ADDRESS, --address ADDRESS
                        Address of WebSockets server.
  -p PORT, --port PORT  Port of WebSockets server.
  --autoofftime AUTOOFFTIME
                        Time (in seconds) for cabin to remain idle before lights are aut omatically shut off.
  --autooffthresh AUTOOFFTHRESH
                        Threshold of movement (in degrees) before idle timer is reset.
```

## Notes
The `arduino.ino` file in this repository is the firmware meant to be flashed to the Arduino to communicate with LightsClient.
