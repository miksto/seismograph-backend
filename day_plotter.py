import asyncio
import websockets
import json
import os

import numpy
from obspy import UTCDateTime, read, Trace, Stream, imaging
import datetime

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client

from obspy import read

import datetime
from pytz import timezone

from obspy import UTCDateTime

def current_date_time():
    return datetime.datetime.now(tz=timezone('Asia/Tokyo'))

mseed_directory = 'files/mseed'
url = f'http://128.199.197.181:8080/mseed/day_14.mseed'
st = read(url)

# client = Client("IRIS")
# cat = client.get_events(
#                   starttime=st[0].stats.starttime,
#                   endtime=st[0].stats.endtime,
#                   latitude=35.6895,
#                   longitude=139.6917,
#                   maxradius=10,
#                   minmagnitude=4
#                   )

st.plot(
  starttime=UTCDateTime("2018-11-14T10:9:00"),
  endtime=UTCDateTime("2018-11-14T10:11:00")
)

# read("files/mseed/hour_2.mseed").plot()