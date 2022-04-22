// ToDo: Read https://stackoverflow.com/questions/25612452/html5-canvas-game-loop-delta-time-calculations - GameLoop

/*
Input processing with django:
Each tick (like 60 times a second) we must send player inputs to the server.
We would loose some data if we only sent the last key press recorded, for example, if the player manages
to press multiple keys during one tick. Therefore, and to make things even less transparent on the client side
(which is a good thing), we just want to record every input and store them in arrays:
    let mouseX = [100, 100.5, 101]
    let keyStrokes = [{'s', 'release', 0.001}, {'w', 'press', 0.002}] // key, action, time (either within tick or some other sort) (maybe already too complex...)
All this will then be processed by the server and send back to the client for the next / in the same (?) tick
*/

// Config
const fov = Math.PI / 3;
const mapHeight = 16;
const mapWidth = 16;
const max_objects = 100;

// Runtime variables
let lastFrameTime;
let mapString;
let map_numbers;

// Received from backend each frame
let playerX;
let playerY;
let playerAngle;
let objects;
let objectCount;
let opponents;
let currWeapon;
let health;
let healthTextBounds;
let ammo;               // ToRefactor: Merge a padded sprite and its bounds into a new class
let ammoTextBounds;
let weaponImageBounds;

async function init()
{    
    socketHandler_init();

    await spriteReader_init();
    
    initRuntimeVariables();
    // Need to wait for spriteReader_init()
    initMap(); // To be moved to backend

    drawingHandler_init(); // Needs to wait for initRuntimeVariables();

    inputHander_init(); // Needs to wait for drawingHandler_init()

    gameLoop();
}

function initRuntimeVariables()
{
    initObjects();

    ammo = 200;
    health = 200;
    currWeapon = 2;
    objectCount = 0;

    //#region Init Textures with their biggest size
    let healthText = getHealthText();
    healthTextBounds_sizeX = healthText[0].length;
    healthTextBounds_sizeY = healthText.length;

    let ammoText = getAmmoText();
    ammoTextBounds_sizeX = ammoText[0].length;
    ammoTextBounds_sizeY = ammoText.length;

    weaponImageBounds = [218, 151];
    //#endregion

    lastFrameTime = Date.now();
}

function initObjects()
{
    objects = [];
    for (let i = 0; i < max_objects; i++)
        objects.push([-10, -10, -1]);
}

function getHealthText()
{
    return font.getTextImg(health.toString()/*.padStart(3, '0')*/ + '%');
}

function getAmmoText()
{
    return font.getTextImg(ammo.toString()/*.padStart(3, '0')*/);
}


function initMap()
{
    mapString =
    "################" +
    "#..............#" +
    "#........#######" +
    "#..............#" +
    "#..............#" +
    "#.....##.......#" +
    "#.....##.......#" +
    "#..............#" +
    "#..............#" +
    "#..............#" +
    "######.........#" +
    "#....#.........#" +
    "#....#.........#" +
    "#............###" +
    "#............###" +
    "################";

    map_numbers = new Array(mapString.length);
    for(i = 0; i < map_numbers.length; i++)
        map_numbers[i] = mapString.charCodeAt(i);

    //movingObjects = [
    //    new MovingObject(8.5, 8.5, bulletSprite),
    //    new MovingObject(7.5, 7.5, bulletSprite)
    //]
}

function gameLoop()
{
    requestAnimationFrame(gameLoop, canvas);

    let currFrameTime = Date.now()
    let deltaTime = currFrameTime - lastFrameTime;
    lastFrameTime = currFrameTime;
    //console.log('fps Frontend: ' + 1000 / deltaTime);
    
    //inputHandler_updateInput(deltaTime);

    drawingHandler_drawCells();
    
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