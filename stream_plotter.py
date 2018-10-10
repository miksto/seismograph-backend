import os
from obspy import UTCDateTime, read, Trace, Stream, imaging
from obspy.clients.fdsn import Client

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
IMAGE_DIRECTORY = 'files/images'

class StreamPlotter:
  
  @staticmethod
  def create_dirs():
    if not os.path.exists(IMAGE_DIRECTORY):
      os.makedirs(IMAGE_DIRECTORY)

  @staticmethod
  async def save_day_plot(stream):
    starttime = stream[0].stats.starttime
    endtime = stream[0].stats.endtime

    image_file_name = IMAGE_DIRECTORY + '/day_' + str(starttime.datetime.day) + '.svg'
    try:
      client = Client("IRIS")
      cat = client.get_events(
                        starttime=starttime,
                        endtime=endtime,
                        latitude=35.6895,
                        longitude=139.6917,
                        maxradius=10,
                        minmagnitude=4
                        )
      stream.plot(
        size=(1280, 960),
        type="dayplot", 
        outfile=image_file_name,
        events=cat,
        vertical_scaling_range=200,
        )
    except Exception as e:
      print("Failed to plot day plot.", e)

  @staticmethod
  async def save_hour_plot(stream, hour):
    image_file_name = IMAGE_DIRECTORY + '/hour_' + str(hour) + '.svg'
    endtime = stream[0].stats.endtime
    stream.plot(
      size=(1280, 250),
      outfile=image_file_name,
      starttime=(endtime-60*60),
      endtime=endtime)

  @staticmethod
  async def save_10_minute_plot(stream):
    # Always create latest.png from last minute
    image_file_name = IMAGE_DIRECTORY + '/latest.svg'
    endtime = stream[0].stats.endtime
    starttime = (endtime-(10*60))
    stream.plot(
      size=(1280, 250),
      outfile=image_file_name,
      starttime=starttime, 
      endtime=endtime)