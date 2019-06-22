import os
import asyncio
import websockets
from http import HTTPStatus
from websockets import ConnectionClosed
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import InvalidHandshake
import json
import datetime
from stream_plotter import StreamPlotter
from stream_manager import StreamManager

WEB_CLIENT_HISTORY_LENGTH = 300
WS_CLIENT_PATH = '/ws/web-client'
WS_DATA_LOGGER_PATH = '/ws/data-logger'
AUTH_TOKEN_HEADER = 'AUTH_TOKEN'

def create_folders():
  StreamManager.create_dirs()
  StreamPlotter.create_dirs()

class AuthenticatingWebSocket(WebSocketServerProtocol):
  def process_request(self, path, request_headers):
    if path not in [WS_CLIENT_PATH, WS_DATA_LOGGER_PATH]:
      return HTTPStatus.NOT_FOUND, []
    if path == WS_DATA_LOGGER_PATH and \
        not request_headers['Authorization'] == os.environ.get(AUTH_TOKEN_HEADER):
        return HTTPStatus.UNAUTHORIZED, []
    else:
      return None

  
class SeismoServer:

  web_clients = set()
  stream_manager = StreamManager()
  last_saved_hour = datetime.datetime.today().hour
  last_saved_minute  = datetime.datetime.today().minute

  def start_server(self):
    start_server = websockets.serve(self.socket_handler, '0.0.0.0', 3000, create_protocol=AuthenticatingWebSocket)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

  async def append_values(self, values):
    await self.stream_manager.append_values(values)
    await self.save_plots_and_mseed()
    await self.publish_data_to_webclients(values)

  async def save_plots_and_mseed(self):
    current_minute = datetime.datetime.today().minute
    current_hour = datetime.datetime.today().hour

    if self.last_saved_minute != current_minute:
      await StreamPlotter.save_last_10_minutes_plot(await self.stream_manager.get_wrapped_stream())
      await StreamPlotter.save_last_60_minutes_plot(await self.stream_manager.get_wrapped_stream())
      await self.stream_manager.save_to_file()
      self.last_saved_minute = current_minute

    if self.last_saved_hour != current_hour:
      await StreamPlotter.save_hour_plot(await self.stream_manager.get_wrapped_stream(), self.last_saved_hour)
      self.last_saved_hour = current_hour

    if not self.stream_manager.is_valid_for_current_date():
      await StreamPlotter.save_day_plot(await self.stream_manager.get_wrapped_stream())
      
      self.stream_manager.begin_new_stream()
      await self.stream_manager.save_to_file()

  def register_web_client(self, websocket):
    print("Registering client")
    self.web_clients.add(websocket)

  def unregister_web_client(self, websocket):
    print("Unregistering client")
    self.web_clients.remove(websocket)

  async def publish_data_to_webclients(self, values):
    old_connections = set()
    for client in self.web_clients:
      try:
        message = json.dumps({'type': 'data', 'values': values})
        await client.send(message)
      except ConnectionClosed:
        old_connections.add(client)

    for client in old_connections:
      self.unregister_web_client(client)

  async def send_history(self, websocket):
    stream = await self.stream_manager.get_wrapped_stream()
    data_list = stream[0].data.tolist()
    message = json.dumps({
      'type': 'data',
      'values': data_list[-WEB_CLIENT_HISTORY_LENGTH:]
    })
    await websocket.send(message)

  async def socket_handler(self, websocket, path):
    if path == WS_CLIENT_PATH:
      self.register_web_client(websocket)
      await self.send_history(websocket)
      # Keep to websocket open
      while True:
          message = await websocket.recv()
    elif path == WS_DATA_LOGGER_PATH:
      async for message in websocket:
        json_data = json.loads(message)
        await self.append_values(json_data['values'])
    else:
      print("Invalid path", path)

if 'AUTH_TOKEN' not in os.environ:
  print("Missing AUTH_TOKEN as environment variable")
else:
  create_folders()
  SeismoServer().start_server()
