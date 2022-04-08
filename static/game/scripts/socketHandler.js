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
        let data = JSON.parse(e.data)

        let mouseDeltaX = lastRecordedMouseX - lastMouseX;
        lastMouseX = lastRecordedMouseX

        webSocket.send(JSON.stringify({
            "type" : "loop",
            "msg"  : {
                "up" : keyStates[87] | false,
                "down" : keyStates[83] | false,
                "left" : keyStates[65] | false,
                "right" : keyStates[68] | false,
                "mouseDeltaX" : mouseDeltaX
            }
        }));
        console.log('Data:', data)
    };

    webSocket.onclose = function(e) {
        console.log('The socket closed unexpectedly')
    };
}