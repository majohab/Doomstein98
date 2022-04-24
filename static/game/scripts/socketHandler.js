const channel_key             = 'c';
const click_key               = 'c';
const down_key                = 'd';
const group_key               = 'g';
const inactive_key            = 'i';
const left_key                = 'l';
const loose_key               = 'l';
const lobby_key               = 'l';
const mouseDelta_key          = 'm';
const message_key             = 'm';
const map_key                 = 'm';
const name_key                = 'n';
const player_key              = 'p';
const right_key               = 'r';
const state_key               = 's';
const time_key                = 't';
const type_key                = 't';
const update_key              = 'u';
const up_key                  = 'u';
const weapon_key              = 'w';
const win_key                 = 'w';
const joinLobby_key           = 'jL';
const joinGame_key            = 'jG';
const ammo_key                = 'a';
const bullet_key              = 'b';
const corpses_key             = 'c';
const duration_key            = 'd';
const direction_key           = 'd';
const health_key              = 'h';
const kills_key               = 'k';
const x_coordinate_key        = 'x';
const y_coordinate_key        = 'y';
const justShot_animation      = 's_a';
const justHit_animation       = 'h_a';
const weapon_change_animation = 'w_a';

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
                't' : joinLobby_key,
                'm'  : {
                    'l'    : lobbyName,
                }
            })
        );
        webSocket.send(
            JSON.stringify({
                't' : joinGame_key,
                'm'  : {
                    'l'    : lobbyName,
                }
            })
        );
    }

    webSocket.onmessage = (e) => {

        let data = JSON.parse(e.data)

        if (data[type_key] == update_key)
        {

            playerX     = data[player_key][userName][x_coordinate_key];
            playerY     = data[player_key][userName][y_coordinate_key];
            playerAngle = data[player_key][userName][direction_key];
            

            initObjects();

            let i = 0;
            let rec_bullets = data[bullet_key];
            for (i = 0; i < rec_bullets.length && i < max_objects; i++)
                objects[i] = [rec_bullets[i][x_coordinate_key], rec_bullets[i][y_coordinate_key], 0];
            o = rec_bullets.length;

            let rec_users = data[player_key];
            for (users_name in rec_users)
            {
                if (users_name != userName && i < max_objects)
                {
                    objects[i] = [rec_users[users_name][x_coordinate_key], rec_users[users_name][y_coordinate_key], 1]
                    i++;
                }
            }

            objectCount = i;


            ammo        = data[player_key][userName][ammo_key];
            health      = data[player_key][userName][health_key];
            currWeapon  = data[player_key][userName][weapon_key];

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

            // Mousewheel
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
                        't' : update_key, // update
                        'm'  : {
                            'u' : keyStates[87] | false, //Up
                            'd' : keyStates[83] | false, //Down
                            'l' : keyStates[65] | false, //left   
                            'r' : keyStates[68] | false, //right
                            'w' : new_idx % 3,           //weapon
                            'm' : ((mouseDeltaX) ? mouseDeltaX : 0), //mouseDelta
                            'c' :  longClicked || shortClicked,      //click
                        }
                    }
                )
            );

            if(shortClicked) {
                shortClicked = false;
            }
        
            //console.log('Data:', data);
        }
    };

    webSocket.onclose = function(e) {
        console.log('The socket closed unexpectedly')
    };
}