function socketHandler_init()
{
    const lobbyName = JSON.parse(document.getElementById('json-lobbyname').textContent);
    document.title = lobbyName;

    const protocol = window.location.protocol.match(/^https/) ? 'wss' : 'ws'

    const webSocket = new WebSocket(
        protocol
        + '://'
        + window.location.host
        + '/ws/game/'
        + lobbyName
        + '/'
    );

    username = "user1"

    webSocket.onopen = function(){ 
        webSocket.send(JSON.stringify({
        "type" : "join",
        "msg"  : {
            "username" : username
        }
        }));
        console.log("SENDEN")
    }

    webSocket.onmessage = function(e) {
        let data = JSON-parse(e.data)
        console.log('Data:', data)
    };

    webSocket.onclose = function(e) {
        console.log('The socket closed unexpectedly')
    };
}