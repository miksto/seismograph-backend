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

current_hour = datetime.datetime.today().hour
history = []

def create_folders():
  if not os.path.exists(mseed_directory):
    os.makedirs(mseed_directory)

  if not os.path.exists(image_directory):
    os.makedirs(image_directory)

def create_stream_from_list(data_list):
  stream = Stream()
  data = numpy.array(data_list, dtype='int16')
  stats = {'network': 'BW', 'station': 'RJOB', 'location': '',
          'channel': 'WLZ', 'npts': len(data_list), 'sampling_rate': 10,
          'mseed': {'dataquality': 'D'}}
  stats['starttime'] = UTCDateTime()
  stream.append(Trace(data=data, header=stats))
  return stream

def start_server():
  start_server = websockets.serve(socket_handler, '0.0.0.0', 3000)
  asyncio.get_event_loop().run_until_complete(start_server)
  asyncio.get_event_loop().run_forever()

def save_plot():
  global current_hour
  new_current_hour = datetime.datetime.today().hour

  # Always create latest.png from last minute
  stream = create_stream_from_list(history[-3000:])
  image_file_name = image_directory + '/latest.png'
  stream.plot(outfile=image_file_name)

  if current_hour != new_current_hour:
    stream = create_stream_from_list(history)
    # New hour. Clear history and save mseed file
    current_hour = new_current_hour
    mseed_file_name = mseed_directory + '/hour_' + str(current_hour) + '.mseed'
    stream.write(mseed_file_name)

    image_file_name = image_directory + '/hour_' + str(current_hour) + '.png'
    stream.plot(outfile=image_file_name)

    history.clear()


def append_value(value):
  history.append(value)
  # Every minute
  if len(history) % 600 == 0:
    save_plot()

async def socket_handler(websocket, path):
  sockdata = await websocket.recv()
  json_data = json.loads(sockdata)
  append_value(json_data['value'])

create_folders()
start_server()

