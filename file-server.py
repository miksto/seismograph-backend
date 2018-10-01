import socketserver
import http.server
import os

files = 'files/images'

if not os.path.exists(files):
  os.makedirs(files)

# Start web server serving images
os.chdir(files)
Handler = http.server.SimpleHTTPRequestHandler
httpd = socketserver.TCPServer(("", 8080), Handler)
print("serving at port", 8080)
httpd.serve_forever()