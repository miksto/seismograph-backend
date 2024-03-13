import os
import sys

from src.client.create_web_api_socket import start_websocket_and_logger
from src.shared.Constants import SEISMOMETER_IDS

if __name__ == "__main__":
    # websocket.enableTrace(True)
    if 'API_ENDPOINT' not in os.environ:
        print("No API_ENDPOINT defined as env var")
    if 'AUTH_TOKEN' not in os.environ:
        print("No AUTH_TOKEN defined as env var")
    else:
        seismometer_id = sys.argv[1]
        if seismometer_id in SEISMOMETER_IDS:
            start_websocket_and_logger(seismometer_id)
        else:
            print("Invalid seismometer_id:", seismometer_id)
