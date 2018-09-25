const os = require('os');
const http = require('http');

const port = 3000;
const hostname = os.hostname();

const server = http.createServer((req, res) => {
    res.statusCode = 200;
    res.setHeader('Content-Type', 'text/plain');
    res.end('Hello World\n');
  });

server.listen(port, hostname, () => {
    console.log('Server running at http://127.0.0.1:' + port)
});