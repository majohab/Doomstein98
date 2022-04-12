function socketHandler_init()
{
    const lobbyName = JSON.parse(document.getElementById('json-lobbyname').textContent);
    const username = "user1"; //temporary variable
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

    webSocket.onopen = function(){ 
        webSocket.send(
            JSON.stringify({
                "type" : "joinLobby",
                "msg"  : {
                    "lobby"    : lobbyName,
                }
            })
        );
        webSocket.send(
            JSON.stringify({
                "type" : "joinGame",
                "msg"  : {
                    "lobby"    : lobbyName,
                }
            })
        );
    }

    webSocket.onmessage = function(e) {
        let data = JSON.parse(e.data)

        playerX     = data['players']['user1']['x'];
        playerY     = data['players']['user1']['y'];
        playerAngle = data['players']['user1']['dir'];

        let mouseDeltaX = lastRecordedMouseX - lastMouseX;
        lastMouseX = lastRecordedMouseX

        //console.log("pointerLocked     : " + pointerLocked)
        //console.log("pointerLockedClick: " + pointerLockedClick)
        //console.log("mouseDeltaX: " + mouseDeltaX)

        webSocket.send(JSON.stringify({
            "type" : "loop",
            "msg"  : {
                "up" : keyStates[87] | false,
                "down" : keyStates[83] | false,
                "left" : keyStates[65] | false,
                "right" : keyStates[68] | false,
                "mouseDeltaX" : ((mouseDeltaX) ? mouseDeltaX : 0),
                "leftClick" :  longClicked || shortClicked,
            }
        }));

        if(shortClicked) {
            shortClicked = false;
        }

        console.log('Data:', data)
    };

    webSocket.onclose = function(e) {
        console.log('The socket closed unexpectedly')
    };
}