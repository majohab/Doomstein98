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

        if (data['type'] == 'update')
        {

            playerX     = data['players'][userName]['x'];
            playerY     = data['players'][userName]['y'];
            playerAngle = data['players'][userName]['dir'];
            

            initBullets();
            let rec_bullets = data['bullets'];
            for (let i = 0; i < rec_bullets.length && i < max_bullets; i++)
                bullets[i] = [rec_bullets[i]['x'], rec_bullets[i]['y']];
            
            bulletCount = rec_bullets.length;

            initopponents();
            let rec_users = data['players'];
            let i = 0;
            for (users_name in rec_users)
            {
                if (users_name != userName && i < max_opponents)
                {
                    opponents[i] = [rec_users[users_name]['x'], rec_users[users_name]['y']]
                    i++;
                }
            }
            opponentsCount = opponents.length;

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

            let new_idx = false

            // E key
            if(keyStates[69]){
                new_idx = weapons[(weapons.indexOf(currWeapon_str) + 1)%weapons.length]
            }

            // Q Key
            if(keyStates[81]){
                new_idx = weapons.indexOf(currWeapon_str) - 1;

                if(new_idx < 0){
                    new_idx += weapons.length;
                }
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
                            "change"        : new_idx,
                            "mouseDeltaX"   : ((mouseDeltaX) ? mouseDeltaX : 0),
                            "leftClick"     :  longClicked || shortClicked,
                        }
                    }
                )
            );

            if(shortClicked) {
                shortClicked = false;
            }
        }
    };

    webSocket.onclose = function(e) {
        console.log('The socket closed unexpectedly')
    };
}