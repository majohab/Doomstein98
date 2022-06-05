//Key constants for transmitted and recieved JSON-Data
const mov_b_anim_key          = 'b';
const channel_key             = 'c';
const click_key               = 'c';
const dead_key                = 'd';
const died_anim_key           = 'd';
const down_key                = 'd';
const event_key               = 'e';
const group_key               = 'g';
const hit_anim_key            = 'h';
const init_key                = 'y';
const inactive_key            = 'i';
const killer_key              = 'k';
const left_key                = 'l';
const loose_key               = 'l';
const lobby_key               = 'l';
const mouseDelta_key          = 'm';
const message_key             = 'm';
const map_key                 = 'm';
const name_key                = 'n';
const mov_p_anim_key          = 'p';
const player_key              = 'p';
const right_key               = 'r';
const shot_anim_key           = 's';
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
const direction_view_key      = 'v';
const direction_move_key      = 'm';
const health_key              = 'h';
const kills_key               = 'k';
const x_coordinate_key        = 'x';
const y_coordinate_key        = 'y';
const justShot_animation      = 's_a';
const justHit_animation       = 'h_a';
const weapon_change_animation = 'w_a';
const move_animation_key      = 'm_a';

 // Init animation times with default values, but will be overriden
let weaponImageAnimationTime = 1;
let playerWalkingAnimationTime = 1;
let bulletFlyingAnimationTime = 1;
let corpseTotalAnimationTime = 1;
let deadTotalTime = 1;

//Boxes for the different game objects
let rec_corpses = [];
let rec_bullets = [];
let rec_opponents = [];
let rec_boxes = [];
let currDeadTime;

//function handling the input of the user and the recieved data from server
function socketHandler_init()
{
    const lobbyName = JSON.parse(document.getElementById('json-lobbyname').textContent);
    const userName  = JSON.parse(document.getElementById('json-username').textContent);
    document.title = lobbyName;
    const protocol = window.location.protocol.match(/^https/) ? 'wss' : 'ws'

    //init state for changing the weapon
    let keyState69 = false
    let keyState81 = false
    let keyState49 = false
    let keyState50 = false
    let keyState51 = false

    //create a connection with the server
    const webSocket = new WebSocket(
        protocol
        + '://'
        + window.location.host
        + '/ws/game/'
        + lobbyName
        + '/'
    );

    //if the connection was successful, send some basic information about the lobby the user is trying to join
    webSocket.onopen = function(){ 

        webSocket.send(
            JSON.stringify({
                't' : joinLobby_key,
                'm'  : {
                    'l'    : lobbyName,
                }
            })
        );
    }

    // called if the user recieved any message from the server
    webSocket.onmessage = (e) => {

        let data = JSON.parse(e.data)

        // if the package contains game information to update the game and the game is still going on
        if (data[type_key] == update_key && gameState < 3)
        {
            // if no map was yet recieved
            if (mapString == null)
            {
                //console.log(data);
                function initValueIfReceived(key, func)
                {
                    if (data[init_key] != null && data[init_key][key] != null)
                        func(data[init_key][key]);
                    else
                        console.log('Cannot initialize init value for key ' + key + ': Value was not received');
                }

                initValueIfReceived(map_key, (data) => onMapReceived(data['l'], data['m']));
                //initValueIfReceived(hit_anim_key, );
                initValueIfReceived(shot_anim_key, (data) => weaponImageAnimationTime = data);
                initValueIfReceived(died_anim_key, (data) => corpseTotalAnimationTime = deadTotalTime = data);
                initValueIfReceived(mov_b_anim_key, (data) => bulletFlyingAnimationTime = data);
                initValueIfReceived(mov_p_anim_key, (data) => playerWalkingAnimationTime = data);
            }       

            // look for all opponents in the data which was recieved and save them in an array
            let rec_opponents_tmp = data[player_key]
            rec_opponents = [];
            for (users_name in rec_opponents_tmp)
            {
                if (users_name != userName)
                    rec_opponents.push(rec_opponents_tmp[users_name]);
            }

            // save other objects in a list
            rec_corpses = data[corpses_key];
            rec_bullets = data[bullet_key];
            rec_boxes = data[ammo_key];
            
            // declare the game as waiting
            // either game has not started yet or the player was killed
            gameState = 1;
            if (waiting_countdown_value > 0) gameState = 0;

            //if the user itself is in the array of the corpses
            //which indicates that he is dead, then change the state of the game
            for (corpse of rec_corpses)
            {
                if (corpse[player_key] == userName)
                {
                    gameState = 2;
                    currDeadTime = corpse[duration_key];

                    break;
                }
            }

            //if the game needs to be updated because player is playing or he is dead and viewing the game
            // change all current states with data from server
            if (gameState < 2)
            {
                playerX     = data[player_key][userName][x_coordinate_key];
                playerY     = data[player_key][userName][y_coordinate_key];
                playerAngle = data[player_key][userName][direction_view_key];   

                ammo        = data[player_key][userName][ammo_key];
                health      = data[player_key][userName][health_key];
                currWeapon  = data[player_key][userName][weapon_key];
                weaponAnimTime = data[player_key][userName][justShot_animation];
            }

            // if the player has to wait because either he is dead or game has not started yet
            waiting_countdown_value = data[duration_key];

            // calculate the delta of the mouse movement
            let mouseDeltaX = lastRecordedMouseX - lastMouseX;
            lastMouseX = lastRecordedMouseX;

            // get index of the current weapon from server
            let new_idx = currWeapon

            //following logic handels the change of the weapon

            // Mousewheel
            // relative index
            if(mouseWheelDelta > 0){
                new_idx += 1
                mouseWheelDelta = 0
            }else if(mouseWheelDelta < 0){
                new_idx -= 1
                mouseWheelDelta = 0
            }

            // E key
            // relative index
            if(keyStates[69] && !(keyState69)){
                new_idx += 1
                keyState69 = true
            }else if(!keyStates[69]){
                keyState69 = false
            }

            // 1 key
            // absolute index
            if(keyStates[49] && !(keyState49)){
                new_idx = 0
                keyState49 = true
            }else if(!keyStates[49]){
                keyState49 = false
            }


            // 2 key
            // absolute index
            if(keyStates[50] && !(keyState50)){
                new_idx = 1
                keyState50 = true
            }else if(!keyStates[50]){
                keyState50 = false
            }


            // 3 key
            // absolute index
            if(keyStates[51] && !(keyState51)){
                new_idx = 2
                keyState51 = true
            }else if(!keyStates[51]){
                keyState51 = false
            }


            // Q Key
            // relative index
            if(keyStates[81] && !(keyState81)){
                new_idx -= 1
                keyState81 = true
            }else if(!keyStates[81]){
                keyState81 = false
            }

            // Send to server the current inputs
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

            //For long click
            if(shortClicked) {
                shortClicked = false;
            }
        
            //console.log('Data:', data);
            //console.log(data[player_key][userName][justShot_animation]);
        }else if(data[type_key] == message_key){
            //TODO: Was soll passieren wenn er eine Nachricht erhält: Lobby kann nicht gefunden werden
            console.log(data[message_key]);
            window.location.replace(window.location.href.replace(/game([\s\S]*)$/ ,'menu/'));
        }else if(data[type_key] == event_key){
            gameState = 2;
        }else if(data[type_key] == win_key){
            gameState = 3;
            console.log(data);
        }else if(data[type_key] == loose_key){
            gameState = 4;
            console.log(data);
        }
    };

    //if websocket was closed
    webSocket.onclose = function(e) {
        console.log('The socket closed unexpectedly')
    };
}