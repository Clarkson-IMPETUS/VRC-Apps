# VRC-Apps.NL2Bridge

Sends orientation data from NoLimits 2 to a VRC-Apps.Server instance.

## Requirement Installation

Scipy is require for this application to work. It is not included as a mandatory dependency due to the discontinuation of wheels for 32-bit Windows, which the Control PC requires.

```bash
pip install scipy
```

## Usage
```console
python -m VRC-Apps.NL2Bridge -h
usage: __main__.py [-h] [--refreshrate REFRESHRATE] [--retryinterval RETRYINTERVAL] [--wsaddress WSADDRESS]
                   [--wsport WSPORT] [--nl2address NL2ADDRESS] [--nl2port NL2PORT]

optional arguments:
  -h, --help            show this help message and exit
  --refreshrate REFRESHRATE
                        Frequency at which status is requested from the server in hz.
  --retryinterval RETRYINTERVAL
                        Delay in seconds between attempts to reconnect to the NoLimits 2 server.
  --wsaddress WSADDRESS
                        Address of WebSockets server.
  --wsport WSPORT       Port of WebSockets server.
  --nl2address NL2ADDRESS
                        Address of the NoLimits 2 telemetry server.
  --nl2port NL2PORT     Port of the NoLimits 2 telemetry server.
```
