# Seismograph Backend

This is the backend implementation for a seismograph I built, as well as the python script for capturing data form the seismometer and submitting it to the backend.

You will find a more detailed description of the seismometer at [miksto.github.com/seismometer](miksto.github.com/seismometer)

I essence this backend receives data from the script [seism_logger.py](seism_logger.py), stores the data as files, and generates various plots to be shown on the web frontend.
For the most part communication with the backend is over a websocket. This allows the web frontend to show a graph that is near realtime displays the data as it is recieved by the backend.
