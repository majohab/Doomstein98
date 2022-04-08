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
        webSocket.send(
            JSON.stringify({
                "type" : "join",
                "msg"  : {
                    "username" : username
                }
            })
        );
    }

    webSocket.onmessage = function(e) {
        let data = JSON.parse(e.data)

        playerX = data['players']['user1']['x'];
        playerY = data['players']['user1']['y'];

        let mouseDeltaX = lastRecordedMouseX - lastMouseX;
        lastMouseX = lastRecordedMouseX

        console.log("pointerLocked     : " + pointerLocked)
        console.log("pointerLockedClick: " + pointerLockedClick)

        webSocket.send(JSON.stringify({
            "type" : "loop",
            "msg"  : {
                "up" : keyStates[87] | false,
                "down" : keyStates[83] | false,
                "left" : keyStates[65] | false,
                "right" : keyStates[68] | false,
                "mouseDeltaX" : ((mouseDeltaX) ? mouseDeltaX : 0),
                "leftClick" :  (pointerLocked ? (pointerLockedClick ? false : clicked) : false) //if the click was to catch the mouse and the mouse has to be catched
            }
        }));

        if(clicked) {
            pointerLockedClick = false;
            clicked = false;
        }
        console.log('Data:', data)
    };

    webSocket.onclose = function(e) {
        console.log('The socket closed unexpectedly')
    };
}