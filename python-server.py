import asyncio
import websockets
import json
import os
from pathlib import Path

import numpy
from obspy import UTCDateTime, read, Trace, Stream, imaging
from obspy.clients.fdsn import Client

import datetime

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

mseed_directory = 'files/mseed'
image_directory = 'files/images'

current_stream = None
last_saved_hour = datetime.datetime.today().hour
last_saved_minute  = datetime.datetime.today().minute

def create_folders():
  if not os.path.exists(mseed_directory):
    os.makedirs(mseed_directory)

  if not os.path.exists(image_directory):
    os.makedirs(image_directory)

def create_new_stream():
  data = numpy.array([], dtype='int16')
  stats = {'network': 'BW', 'station': 'MIK', 'location': '',
          'channel': 'Z', 'npts': len(data), 'sampling_rate': 10,
          'mseed': {'dataquality': 'D'}}
  start_time = datetime.datetime.now()

  stats['starttime'] = UTCDateTime(start_time)
  stream = Stream([Trace(data=data, header=stats)])
  return stream

def stream_file_name(date):
  return mseed_directory + '/day_' + str(date.day) + '.mseed'

def is_stream_date_correct(stream):
  current_date = datetime.datetime.today().date()
  return stream[0].stats.starttime.datetime.date() == current_date


"""
Returs the current_stream variable or reads the stream with correct date from the file if it exists.
If current_stream is None and no valid file exists, a new stream is created but not saved.
"""
def get_current_stream():
  global current_stream

  current_date = datetime.datetime.today().date()
  file_name = stream_file_name(current_date)

  if current_stream is None:
   if Path(file_name).is_file():
    stream = read(file_name, dtype='int16')
    # Stream date must match current date
    if is_stream_date_correct(stream):
      current_stream = stream
  
  # If current_stream still is None, create a new one
  if current_stream is None:
    new_stream = create_new_stream()
    current_stream = new_stream

  return current_stream

def start_server():
  start_server = websockets.serve(socket_handler, '0.0.0.0', 3000)
  asyncio.get_event_loop().run_until_complete(start_server)
  asyncio.get_event_loop().run_forever()

def save_day_plot(stream):
  starttime = stream[0].stats.starttime
  endtime = stream[0].stats.endtime

  image_file_name = image_directory + '/day_' + str(starttime.datetime.day) + '.svg'
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
      outfile=image_file_name,
      events=cat,
      vertical_scaling_range=200,
      )
  except Exception as e:
    print("Failed to plot day plot.", e)

def save_hour_plot(stream):
  image_file_name = image_directory + '/hour_' + str(last_saved_hour) + '.svg'
  endtime = stream[0].stats.endtime
  stream.plot(
    size=(1280, 250),
    outfile=image_file_name,
    starttime=(endtime-60*60),
    endtime=endtime)

def save_10_minute_plot(stream):
  # Always create latest.png from last minute
  image_file_name = image_directory + '/latest.svg'
  endtime = stream[0].stats.endtime
  starttime = (endtime-(10*60))
  stream.plot(
    size=(1280, 250),
    outfile=image_file_name,
    starttime=starttime, 
    endtime=endtime)

def save_mseed_file(stream):
  file_name = stream_file_name(stream[0].stats.starttime.datetime.date())
  stream.write(file_name)

def append_values(values):
  stream = get_current_stream()
  data = numpy.array(values, dtype='int16')
  stream[0].data = numpy.append(stream[0].data, data)
  
  # Update sample rate
  time_delta = (datetime.datetime.now() - stream[0].stats.starttime.datetime).total_seconds()
  sampling_rate = stream[0].stats.npts / time_delta
  stream[0].stats.sampling_rate = sampling_rate

  # Plot graphs and save data to file
  save_plots_and_mseed(stream)

def save_plots_and_mseed(stream):
  global current_stream, last_saved_hour, last_saved_minute

  current_minute = datetime.datetime.today().minute
  current_hour = datetime.datetime.today().hour

  if last_saved_minute != current_minute:
    save_10_minute_plot(stream)
    save_mseed_file(stream)
    last_saved_minute = current_minute

  if last_saved_hour != current_hour:
    save_hour_plot(stream)
    last_saved_hour = current_hour

  if not is_stream_date_correct(stream):
    save_day_plot(stream)
    current_stream = create_new_stream()
    current_stream.write(stream_file_name(datetime.datetime.today().date))

async def socket_handler(websocket, path):
  while True:
    sockdata = await websocket.recv()
    json_data = json.loads(sockdata)
    append_values(json_data['values'])

create_folders()
start_server()
