function socketHandler_init()
{
    const lobbyName = JSON.parse(document.getElementById('json-lobbyname').textContent);
    const userName  = JSON.parse(document.getElementById('json-username').textContent);
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

        console.log('Username:', userName)

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

    webSocket.onmessage = (e) => {

        let data = JSON.parse(e.data)

        playerX     = data['players'][userName]['x'];
        playerY     = data['players'][userName]['y'];
        playerAngle = data['players'][userName]['dir'];
        

        let rec_bullets = data['bullets'];
        initBullets();
        for (let i = 0; i < rec_bullets.length && i < max_bullets; i++)
            bullets[i] = [rec_bullets[i]['x'], rec_bullets[i]['y']];
        
        bulletCount = rec_bullets.length;

        ammo        = data['players'][userName]['ammo'];
        health      = data['players'][userName]['h'];
        currWeapon_str  = data['players'][userName]['weapon'];
        weapons     = data['players'][userName]['weapons'];

        currWeapon = weapons.indexOf(currWeapon_str);

        let mouseDeltaX = lastRecordedMouseX - lastMouseX;
        lastMouseX = lastRecordedMouseX

        //console.log("pointerLocked     : " + pointerLocked)
        //console.log("pointerLockedClick: " + pointerLockedClick)
        //console.log("mouseDeltaX: " + mouseDeltaX)

        let new_idx = currWeapon

        // E key
        // Relative Index
        if(keyStates[69]){
            new_idx += 1
        }

        // 1 key
        // Relative Index
        if(keyStates[49]){
            new_idx = 1
        }

        // 2 key
        // Relative Index
        if(keyStates[49]){
            new_idx = 2
        }

        // 3 key
        // Relative Index
        if(keyStates[49]){
            new_idx = 3
        }

        // Q Key
        // Relative Index
        if(keyStates[81]){
            new_idx -= 1
        }

        webSocket.send(
            JSON.stringify(
                {
                    "type" : "loop",
                    "msg"  : {
                        "up"            : keyStates[87] | false,
                        "down"          : keyStates[83] | false,
                        "left"          : keyStates[65] | false,
                        "right"         : keyStates[68] | false,
                        "weapon"        : new_idx,
                        "mouseDeltaX"   : ((mouseDeltaX) ? mouseDeltaX : 0),
                        "leftClick"     :  longClicked || shortClicked,
                    }
                }
            )
        );

        if(shortClicked) {
            shortClicked = false;
        }
        
        //console.log('Data:', data)
    };

    webSocket.onclose = function(e) {
        console.log('The socket closed unexpectedly')
    };
}