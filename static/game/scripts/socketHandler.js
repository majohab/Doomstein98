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
            

            initObjects();

            let i = 0;
            let rec_bullets = data['bullets'];
            for (i = 0; i < rec_bullets.length && i < max_objects; i++)
                objects[i] = [rec_bullets[i]['x'], rec_bullets[i]['y'], 0];
            o = rec_bullets.length;

            let rec_users = data['players'];
            for (users_name in rec_users)
            {
                if (users_name != userName && i < max_objects)
                {
                    objects[i] = [rec_users[users_name]['x'], rec_users[users_name]['y'], 1]
                    i++;
                }
            }

            objectCount = i;


            ammo        = data['players'][userName]['ammo'];
            health      = data['players'][userName]['h'];
            currWeapon  = data['players'][userName]['weapon'];

            let mouseDeltaX = lastRecordedMouseX - lastMouseX;
            lastMouseX = lastRecordedMouseX;

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
        
            console.log('Data:', data);
            console.log(data['players'][userName]['cha_weap_an']);
        }
    };

    webSocket.onclose = function(e) {
        console.log('The socket closed unexpectedly')
    };
}