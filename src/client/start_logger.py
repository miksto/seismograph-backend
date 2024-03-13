import os
import sys
from typing import Optional, Callable, Any

import websocket
from websocket import WebSocketApp, WebSocket

from src.client.seism_logger import SeismometerConfig, SeismLogger
from src.shared.Constants import SEISMOMETER_IDS


def create_web_api_socket(seismometer_id: str, on_open: Optional[Callable[[WebSocket], None]]) -> WebSocketApp:
    def on_message(ws: WebSocket, message: Any):
        print(message)

    def on_error(ws: WebSocket, error: Any):
        print(error)

    def on_close(ws: WebSocket, close_status_code: Any, close_msg: Any):
        print("### closed ###")

    web_socket_url = "wss://" + os.environ.get('API_ENDPOINT') + "/ws/data-logger?seismometer_id=" + seismometer_id
    auth_token = os.environ.get('AUTH_TOKEN')
    ws = websocket.WebSocketApp(web_socket_url,
                                header=["Authorization:" + auth_token],
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)
    return ws


def start_seism_logger(seismometer_id: str) -> None:
    config = SeismometerConfig(seismometer_id)
    print("starting", '\'' + seismometer_id + '\'')

    def on_websocket_open(ws):
        print("websocket open")
        seism_logger = SeismLogger(config, ws)
        seism_logger.start()

    ws = create_web_api_socket(seismometer_id, on_websocket_open)
    ws.run_forever()


if __name__ == "__main__":
    # websocket.enableTrace(True)
    if 'API_ENDPOINT' not in os.environ:
        print("No API_ENDPOINT defined as env var")
    if 'AUTH_TOKEN' not in os.environ:
        print("No AUTH_TOKEN defined as env var")
    else:
        seismometer_id = sys.argv[1]
        if seismometer_id in SEISMOMETER_IDS:
            start_seism_logger(seismometer_id)
        else:
            print("Invalid seismometer_id:", seismometer_id)
