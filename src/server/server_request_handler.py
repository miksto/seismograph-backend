import asyncio
import json
import os
from http import HTTPStatus
from pathlib import Path
from typing import List, Dict, Any, Set
from urllib.parse import urlparse, parse_qs

import websockets
from websockets import ConnectionClosed
from websockets.server import WebSocketServerProtocol

from src.server.seismometer import Seismometer
from src.shared.Constants import SEISMOMETER_IDS

WS_CLIENT_PATH = '/ws/web-client'
WS_DATA_LOGGER_PATH = '/ws/data-logger'
WS_SEISMOMETER_QUERY_PARAM = 'seismometer_id'
WS_HISTORY_LENGTH_QUERY_PARAM = 'history_length'


class AuthenticatingWebSocket(WebSocketServerProtocol):
    def process_request(self, path, request_headers):
        parsed_url = urlparse(path)
        query_params = parse_qs(parsed_url.query)

        if parsed_url.path not in [WS_CLIENT_PATH, WS_DATA_LOGGER_PATH]:
            return HTTPStatus.NOT_FOUND, []

        if WS_SEISMOMETER_QUERY_PARAM not in query_params or \
                query_params[WS_SEISMOMETER_QUERY_PARAM][0] not in SEISMOMETER_IDS:
            return HTTPStatus.NOT_FOUND, []

        if parsed_url.path == WS_DATA_LOGGER_PATH and \
                not request_headers['Authorization'] == os.environ.get('AUTH_TOKEN'):
            return HTTPStatus.UNAUTHORIZED, []

        return None


class ServerRequestHandler:
    seismometers: Dict[str, Seismometer] = {}
    web_clients: Dict[str, Set[WebSocketServerProtocol]] = {}

    def start_server(self) -> None:
        for seismometer_id in SEISMOMETER_IDS:
            seismometer = Seismometer(seismometer_id, Path('files/' + seismometer_id))
            seismometer.create_folders()
            self.seismometers[seismometer_id] = seismometer

        start_server = websockets.serve(self.socket_handler, '0.0.0.0', 3000, create_protocol=AuthenticatingWebSocket)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def handle_data(self, seismometer_id: str, data: Dict[str, Any]) -> None:
        values: List[int] = data['values']
        stats: Dict[str, Any] = data['stats']
        seismometer = self.seismometers[seismometer_id]
        await seismometer.handle_data(values, stats)
        await self.publish_data_to_webclients(seismometer_id, values, stats)

    def register_web_client(self, seismometer_id: str, websocket: WebSocketServerProtocol) -> None:
        print("Registering client")

        if not seismometer_id in self.web_clients.keys():
            self.web_clients[seismometer_id] = set()

        self.web_clients[seismometer_id].add(websocket)

    def unregister_web_client(self, seismometer_id: str, websocket: WebSocketServerProtocol) -> None:
        print("Unregistering client")
        if seismometer_id in self.web_clients.keys():
            self.web_clients[seismometer_id].remove(websocket)

    async def publish_data_to_webclients(self, seismometer_id: str, values: List, stats: Dict[str, Any]) -> None:
        if seismometer_id not in self.web_clients.keys():
            return

        old_connections = set()
        for client in self.web_clients[seismometer_id]:
            try:
                message = json.dumps({
                    'type': 'data',
                    'values': values,
                    'stats': stats
                })
                await client.send(message)
            except ConnectionClosed:
                old_connections.add(client)

        for client in old_connections:
            self.unregister_web_client(seismometer_id, client)

    async def send_history(self, seismometer_id: str, websocket: WebSocketServerProtocol,
                           history_length: int = 30) -> None:
        seismometer = self.seismometers[seismometer_id]
        data_list = await seismometer.get_last_seconds_of_data(history_length)
        message = json.dumps({
            'type': 'data',
            'values': data_list,
            'stats': seismometer.stats
        })
        await websocket.send(message)

    async def socket_handler(self, websocket: WebSocketServerProtocol, path: str) -> None:
        parsed_url = urlparse(path)
        query_params = parse_qs(parsed_url.query)
        seismometer_id = query_params[WS_SEISMOMETER_QUERY_PARAM][0]

        if parsed_url.path == WS_CLIENT_PATH:
            history_length = int(query_params[WS_HISTORY_LENGTH_QUERY_PARAM][0])
            self.register_web_client(seismometer_id, websocket)
            await self.send_history(seismometer_id, websocket, history_length)
            # Keep to websocket open
            while True:
                message = await websocket.recv()
        elif parsed_url.path == WS_DATA_LOGGER_PATH:
            async for message in websocket:
                json_data: Dict[str, Any] = json.loads(message)
                await self.handle_data(seismometer_id, json_data)
        else:
            print("Invalid path", path)
