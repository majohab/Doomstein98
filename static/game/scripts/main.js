// Config
const fov = Math.PI / 3;
const max_corpses = 5;
const max_opponents = 5;
const max_bullets = 10;
const max_boxes = 10;
const maxObjectCount = max_corpses * max_opponents * max_bullets * max_boxes;

// Runtime variables
let lastFrameTime;
let mapString;
let map_numbers;
let mapWidth;    // 87
let mapHeight;   // 38
let gameState = 0; // 0: Not started; 1: Playing; 2: Dead; 3: Won; 4: Lost

// Received from backend each frame
let playerX;
let playerY;
let playerAngle;
let opponents;
let currWeapon;
let health;
let ammo;
let waiting_countdown_value;
let weaponAnimTime;

// Beginning of whole Game Frontend
async function init()
{    
    socketHandler_init();

    await spriteReader_init();
    
    initRuntimeVariables();

    await initMap_Numbers();

    drawingHandler_init(); // Needs to wait for initRuntimeVariables();
    drawingHandler_initKernel();

    inputHander_init(); // Needs to wait for drawingHandler_init()

    gameLoop();
}

function initRuntimeVariables()
{
    gameStarted = false;

    ammo = 200;
    health = 200;
    currWeapon = 2;
    weaponAnimTime = -1;
    waiting_countdown_value = 3
    playerX = playerY = playerAngle = 0;

    lastFrameTime = Date.now();
}


function getHealthText(overrideValue)
{
    let val = health;
    if (overrideValue != null) val = overrideValue;
    return font.getTextImg(val.toString()/*.padStart(3, '0')*/ + '%');
}

function getAmmoText(overrideValue)
{
    let val = ammo;
    if (overrideValue != null) val = overrideValue;
    return font.getTextImg(val.toString()/*.padStart(3, '0')*/);
}

function getWaitingCountdownText(overrideValue)
{
    let val = waiting_countdown_value;
    if (overrideValue != null) val = overrideValue;
    return font.getTextImg(val.toString());
}

function getWaitingInfoText(overrideValue)
{
    let val = rec_opponents.length + 1;
    if (overrideValue != null) val = overrideValue
    return font.getTextImg('waiting for more players... (' + val + ')');
}

function getDeadScreenText(overrideValue)
{
    let val = currDeadTime / 60;
    if (overrideValue != null) val = overrideValue;
    return font.getTextImg('respawning in ' + val.toFixed(1));
}

function onMapReceived(width, map)
{
    mapString = map;

    mapWidth = width;
    mapHeight = mapString.length / mapWidth;
    if (mapHeight % 1 != 0)
    {
        console.error("Map format is not correct: map.length / mapWidth is not an integer");
    }
}

async function initMap_Numbers()
{
    const checkIntervall = 50;
    while(mapString == null)
    {
        await new Promise(resolve => setTimeout(resolve, checkIntervall));
        console.log('Still waiting for map...');
    }

    map_numbers = new Array(mapString.length);
    for(i = 0; i < map_numbers.length; i++)
        map_numbers[i] = mapString.charCodeAt(i);
    
    console.log('Received map');
}

function gameLoop()
{
    requestAnimationFrame(gameLoop, canvas);

    let currFrameTime = Date.now()
    lastFrameTime = currFrameTime;
    //console.log('fps Frontend: ' + 1000 / deltaTime);
    
    //inputHandler_updateInput(deltaTime);

    drawingHandler_draw();
    
    //console.log("forwardX: " + Math.sin(playerAngle) + ", forwardY: " + Math.cos(playerAngle)); 
}

//class MovingObject
//{
//    constructor(x, y, sprite)
//    {
//        this.x = x;
//        this.y = y;
//        this.spriteIndex = 0;
//        this.spriteHeight = sprite.height;
//        this.spriteWidth = sprite.width;
//    }
//}