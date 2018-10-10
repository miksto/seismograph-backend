import asyncio
import websockets
from websockets import ConnectionClosed
import json
import os
from pathlib import Path
import numpy
from obspy import UTCDateTime, read, Trace, Stream
import datetime
from stream_plotter import StreamPlotter

MSEED_DIRECTORY = 'files/mseed'
WEB_CLIENT_HISTORY_LENGTH = 200

web_clients = set()
current_stream = None
last_saved_hour = datetime.datetime.today().hour
last_saved_minute  = datetime.datetime.today().minute

def create_folders():
  if not os.path.exists(MSEED_DIRECTORY):
    os.makedirs(MSEED_DIRECTORY)
  
  StreamPlotter.create_dirs()

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
  return MSEED_DIRECTORY + '/day_' + str(date.day) + '.mseed'

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

async def save_mseed_file(stream):
  file_name = stream_file_name(stream[0].stats.starttime.datetime.date())
  stream.write(file_name)

async def append_values(values):
  stream = get_current_stream()
  data = numpy.array(values, dtype='int16')
  stream[0].data = numpy.append(stream[0].data, data)
  
  # Update sample rate
  time_delta = (datetime.datetime.now() - stream[0].stats.starttime.datetime).total_seconds()
  sampling_rate = stream[0].stats.npts / time_delta
  stream[0].stats.sampling_rate = sampling_rate

  # Plot graphs and save data to file
  await save_plots_and_mseed(stream)
  await publish_data_to_webclients(values)

async def save_plots_and_mseed(stream):
  global current_stream, last_saved_hour, last_saved_minute

  current_minute = datetime.datetime.today().minute
  current_hour = datetime.datetime.today().hour

  if last_saved_minute != current_minute:
    await StreamPlotter.save_10_minute_plot(stream)
    await save_mseed_file(stream)
    last_saved_minute = current_minute

  if last_saved_hour != current_hour:
    await StreamPlotter.save_hour_plot(stream, last_saved_hour)
    last_saved_hour = current_hour

  if not is_stream_date_correct(stream):
    await StreamPlotter.save_day_plot(stream)
    current_stream = create_new_stream()
    current_stream.write(stream_file_name(datetime.datetime.today().date()))

def register_web_client(websocket):
  print("Registering client")
  web_clients.add(websocket)

def unregister_web_client(websocket):
  print("Unregistering client")
  web_clients.remove(websocket)

async def publish_data_to_webclients(values):
  old_connections = set()
  for client in web_clients:
    try:
      message = json.dumps({'type': 'data', 'values': values})
      await client.send(message)
    except ConnectionClosed:
      old_connections.add(client)

  for client in old_connections:
    unregister_web_client(client)

async def send_history(websocket):
  message = json.dumps({
    'type': 'data',
    'values': get_current_stream()[0].data.tolist()[-WEB_CLIENT_HISTORY_LENGTH:]
  })
  await websocket.send(message)

async def socket_handler(websocket, path):
  if path == '/web-client':
    register_web_client(websocket)
    await send_history(websocket)
    # Keep to websocket open
    while True:
        message = await websocket.recv()
  else:
    async for message in websocket:
      json_data = json.loads(message)
      await append_values(json_data['values'])

create_folders()
start_server()
