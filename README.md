# Seismograph Backend

This is the backend implementation for a seismograph I built, including the client that samples the seismometer and
submits the values to the backend.

You will find a more detailed description of the seismometer
at [miksto.github.com/seismometer](https://miksto.github.com/seismometer)

In essence this backend receives data from client, stores the data as files, and
generates various plots to be shown on the web frontend.
For the most part communication with the backend is over a websocket. This allows the web frontend to show a graph that
is near realtime displays the data as it is received by the backend.

# Usage
Start the server by executing one of the following commands

```bash
docker-compose up --build
```

```bash
pipenv run python start_server.py
```

Then in a different shell start the logger with an optionally mocked ADC if you are not running it on a Raspberry Pi .

```bash
pipenv install
pipenv run python start_logger.py vertical_pendulum --mock-adc
```
