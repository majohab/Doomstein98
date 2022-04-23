function socketHandler_init()
{
    const lobbyName = JSON.parse(document.getElementById('json-lobbyname').textContent);
    const userName  = JSON.parse(document.getElementById('json-username').textContent);
    document.title = lobbyName;
    const protocol = window.location.protocol.match(/^https/) ? 'wss' : 'ws'

    let keyState69 = false
    let keyState81 = false
    let keyState49 = false
    let keyState50 = false
    let keyState51 = false

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
            // Relativer Index
            if(keyStates[69] && !(keyState69)){
                new_idx += 1
                keyState69 = true
            }else if(!keyStates[69]){
                keyState69 = false
            }

            if(mouseWheelDelta > 0){
                new_idx += 1
                mouseWheelDelta = 0
            }else if(mouseWheelDelta < 0){
                new_idx -= 1
                mouseWheelDelta = 0
            }

            // 1 key
            // Absoluter Index
            if(keyStates[49] && !(keyState49)){
                new_idx = 0
                keyState49 = true
            }else if(!keyStates[49]){
                keyState49 = false
            }


            // 2 key
            // Absoluter Index
            if(keyStates[50] && !(keyState50)){
                new_idx = 1
                keyState50 = true
            }else if(!keyStates[50]){
                keyState50 = false
            }


            // 3 key
            // Absoluter Index
            if(keyStates[51] && !(keyState51)){
                new_idx = 2
                keyState51 = true
            }else if(!keyStates[51]){
                keyState51 = false
            }


            // Q Key
            // Relativer Index
            if(keyStates[81] && !(keyState81)){
                new_idx -= 1
                keyState81 = true
            }else if(!keyStates[81]){
                keyState81 = false
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
                            "weapon"        : new_idx % 3,
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