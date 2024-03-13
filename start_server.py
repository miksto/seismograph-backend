import os

from src.server.server_request_handler import ServerRequestHandler

if __name__ == "__main__":
    if 'AUTH_TOKEN' not in os.environ:
        print("Missing AUTH_TOKEN as environment variable")
    else:
        ServerRequestHandler().start_server()
