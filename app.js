const os = require('os');
const http = require('http');
const webSocketServer = require('websocket').server;

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


/*
 * Websocket stuff 
 */
var history = [ ];
var historySize = 2000
var clients = [ ];
var publisher = null;

const wsServer = new webSocketServer({httpServer: server});

wsServer.on('request', function(request) {
    console.log((new Date()) + ' Connection from origin ' + request.origin + '.');
    if (request.resource !== '/publisher' 
        && request.resource !== '/subscriber') {
            console.log("Invalid resource: " + request.resource );
            request.reject();
            return;
    }

    const connection = request.accept(null, request.origin); 
    console.log((new Date()) + ' Connection accepted.');

    if (request.resource === '/publisher') {
        publisher = connection;
        connection.on('message', function(message) {
            if (message.type === 'utf8') {
                jsonData = JSON.parse(message.utf8Data);
            
                if (jsonData.type === 'post_data') {
                    console.log("Received data: " + message.utf8Data)
                    history.push(jsonData.value)
                    history = history.slice(-historySize);
                    
                    for (var i=0; i < clients.length; i++) {
                        clients[i].sendUTF(message.utf8Data);
                    }
                } else {
                    console.log("Received invalid payload type: '" + jsonData.type +"'")
                }
            }
        });
        // publisher disconnected
        connection.on('close', function(connection) {
            console.log((new Date()) + " Publisher " + connection.remoteAddress + " disconnected.");
            publisher = null;
        });
    } else if (request.resource === '/subscriber') {
        const index = clients.push(connection) - 1;
        // send back chat history
        if (history.length > 0) {
            connection.sendUTF(
                JSON.stringify({ type: 'history', data: history} )
            );
        }
        // subscriber disconnected
        connection.on('close', function(connection) {
            console.log((new Date()) + " Suscriber " + connection.remoteAddress + " disconnected.");
            clients.splice(index, 1);
        });
    }
});
