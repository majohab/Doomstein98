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

// Runtime variables
let lastFrameTime;
let mapString;
let map_numbers;
let movingObjects;

async function init()
{
    socketHandler_init();

    await spriteReader_init();
    
    // Need to wait for spriteReader_init()
    initMap(); // To be moved to backend
    drawingHandler_init();

    inputHander_init(); // Needs to wait for drawingHandler_init()

    lastFrameTime = Date.now();

    gameLoop();
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

    movingObjects = [
        new MovingObject(8.5, 8.5, bulletSprite),
        new MovingObject(7.5, 7.5, bulletSprite)
    ]
}

function gameLoop()
{
    requestAnimationFrame(gameLoop, canvas);

    let currFrameTime = Date.now()
    let deltaTime = currFrameTime - lastFrameTime;
    lastFrameTime = currFrameTime;
    //console.log('fps: ' + 1000 / deltaTime);
    
    //inputHandler_updateInput(deltaTime);

    drawingHandler_drawCells();

    //console.log("x: " + playerX + ", y: " + playerY);
    //console.log("forwardX: " + Math.sin(playerAngle) + ", forwardY: " + Math.cos(playerAngle)); 
}

class MovingObject
{
    constructor(x, y, sprite)
    {
        this.x = x;
        this.y = y;
        this.spriteIndex = 0;
        this.spriteHeight = sprite.height;
        this.spriteWidth = sprite.width;
    }
}