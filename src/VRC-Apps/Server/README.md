# VRC-Apps.Server

Exposes the following commands of [pyMaxFlight](https://github.com/Clarkson-IMPETUS/pyMaxFlight) using [pyWSConsole](https://github.com/heyjoeway/pyWSConsole):
- liftRaise
- liftStop
- liftLower
- start
- run
- freeze
- stop
- forceRaised
- counterweightFwd
- counterweightBwd
- home
- status
- setRollTarget
  - Parameter: roll (int)
- setPitchTarget
  - Parameter: pitch (int)

# Usage
```console
python -m VRC-Apps.Server
```

For help on further usage (eg. developing a client), connect to the WebSockets server and send `help`. It will return a list of functions with their signatures. Arguments are separated by commas. Please also see [the pyMaxFlight docs](https://pymaxflight.readthedocs.io/en/latest/).
