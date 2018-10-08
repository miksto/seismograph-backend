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

mseed_directory = 'files/mseed'
image_directory = 'files/images'

last_saved_hour = datetime.datetime.today().hour
last_saved_minute  = datetime.datetime.today().minute

history = []

def create_folders():
  if not os.path.exists(mseed_directory):
    os.makedirs(mseed_directory)

  if not os.path.exists(image_directory):
    os.makedirs(image_directory)

def create_stream_from_list(data_list, seconds):
  data = numpy.array(data_list, dtype='int16')
  sampling_rate = len(data_list)/seconds
  
  if sampling_rate == 0:
    print("sampling rate", sampling_rate)
    return

  stats = {'network': 'BW', 'station': 'MIK', 'location': '',
          'channel': 'Z', 'npts': len(data_list), 'sampling_rate': sampling_rate,
          'mseed': {'dataquality': 'D'}}
  start_time = datetime.datetime.now() - datetime.timedelta(seconds=seconds)
  stats['starttime'] = UTCDateTime(start_time)
  stream = Stream([Trace(data=data, header=stats)])
  return stream

def start_server():
  start_server = websockets.serve(socket_handler, '0.0.0.0', 3000)
  asyncio.get_event_loop().run_until_complete(start_server)
  asyncio.get_event_loop().run_forever()

def save_hour_plot():
  global last_saved_hour

  stream = create_stream_from_list(history, 60*60)
  # New hour. Clear history and save mseed file
  mseed_file_name = mseed_directory + '/hour_' + str(last_saved_hour) + '.mseed'
  stream.write(mseed_file_name)

  image_file_name = image_directory + '/hour_' + str(last_saved_hour) + '.png'
  stream.plot(outfile=image_file_name)
  last_saved_hour = datetime.datetime.today().hour

def save_plot():
  global last_saved_hour
  global last_saved_minute

  # Always create latest.png from last minute
  stream = create_stream_from_list(history[-3000:], 5*60)
  image_file_name = image_directory + '/latest.png'
  stream.plot(outfile=image_file_name)
  last_saved_minute = datetime.datetime.today().minute

  current_hour = datetime.datetime.today().hour
  if last_saved_hour != current_hour:
    save_hour_plot()
    history.clear()

def append_values(values):
  history.extend(values)
  # Every minute
  current_minute = datetime.datetime.today().minute
  if len(history) > 0 and last_saved_minute != current_minute:
    save_plot()

async def socket_handler(websocket, path):
  while True:
    sockdata = await websocket.recv()
    json_data = json.loads(sockdata)
    append_values(json_data['values'])

create_folders()
start_server()

