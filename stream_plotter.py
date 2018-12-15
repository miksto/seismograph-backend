import os
from obspy import UTCDateTime, read, Trace, Stream, Catalog
from obspy.clients.fdsn import Client

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
IMAGE_DIRECTORY = 'files/images'

class StreamPlotter:

  @staticmethod
  def get_japan_earthquakes(client, starttime, endtime):
    try:
      return client.get_events(
                      starttime=starttime,
                      endtime=endtime,
                      latitude=35.6895,
                      longitude=139.6917,
                      maxradius=15,
                      maxmagnitude=6
                      )
    except Exception as e:
      print(e)
      return Catalog()
  
  @staticmethod
  def get_global_earthquakes(client, starttime, endtime):
    try:
      return client.get_events(
                      starttime=starttime,
                      endtime=endtime,
                      minmagnitude=6
                      )
    except Exception as e:
      print(e)
      return Catalog()
  
  @staticmethod
  def create_dirs():
    if not os.path.exists(IMAGE_DIRECTORY):
      os.makedirs(IMAGE_DIRECTORY)

  @staticmethod
  async def save_day_plot(stream):
    starttime = stream[0].stats.starttime
    endtime = stream[0].stats.endtime
    print("Plotting day plot for stream with starttime:", starttime)
    image_file_name = IMAGE_DIRECTORY + '/day_' + str(starttime.datetime.day) + '.svgz'

    try:
      client = Client("IRIS")
      cat = StreamPlotter.get_japan_earthquakes(client, starttime, endtime)
      cat += StreamPlotter.get_global_earthquakes(client, starttime, endtime)
        
      stream.plot(
        size=(1280, 960),
        type="dayplot", 
        outfile=image_file_name,
        events=cat,
        vertical_scaling_range=250,
        )
    except Exception as e:
      print("Failed to plot day plot.", e)

  @staticmethod
  async def save_hour_plot(stream, hour):
    image_file_name = IMAGE_DIRECTORY + '/hour_' + str(hour) + '.svgz'
    endtime = stream[0].stats.endtime
    stream.plot(
      size=(1280, 250),
      outfile=image_file_name,
      starttime=(endtime-60*60),
      endtime=endtime)

  @staticmethod
  async def save_last_10_minutes_plot(stream):
    # Always create latest.png from last minute
    image_file_name = IMAGE_DIRECTORY + '/last_10_minutes.svgz'
    endtime = stream[0].stats.endtime
    starttime = (endtime-(10*60))
    stream.plot(
      size=(1280, 250),
      outfile=image_file_name,
      starttime=starttime, 
      endtime=endtime)

  @staticmethod
  async def save_last_60_minutes_plot(stream):
    # Always create latest.png from last minute
    image_file_name = IMAGE_DIRECTORY + '/last_60_minutes.svgz'
    endtime = stream[0].stats.endtime
    starttime = (endtime-(60*60))
    stream.plot(
      size=(1280, 250),
      outfile=image_file_name,
      starttime=starttime, 
      endtime=endtime)
