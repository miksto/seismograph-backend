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
st = Stream()
for i in range(0,24):
  try:
    # url = f"http://46.101.184.224:8080/mseed/hour_{i}.mseed"
    url = f"files/mseed/hour_{i}.mseed"
    new_st = read(url)
    new_st[0].stats.sampling_rate = 10
    new_st[0].stats.station = 'MIK'
    new_st[0].stats.channel = 'Z'
    new_st[0].stats.network = 'BW'
    if (len(st) > 0):
      st[0] += new_st[0]
    else:
      st += new_st
  except Exception as e:
    print(url, "Not found", e)

    # mseed_file_name = mseed_directory + '/hour_' + str(i) + '.mseed'
client = Client("IRIS")
cat = client.get_events(
                  starttime=st[0].stats.starttime,
                  endtime=st[0].stats.endtime,
                  latitude=35.6895,
                  longitude=139.6917,
                  maxradius=10,
                  minmagnitude=4
                  )

print(cat)
st.plot(
  type="dayplot", 
  events=cat,
  vertical_scaling_range=100,
)

# read("files/mseed/hour_2.mseed").plot()