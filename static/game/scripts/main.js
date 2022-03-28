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
const map = [];

// Runtime variables
let canvas;
let lastFrameTime;

function init()
{
    socketHandler_init();

    canvas = document.getElementById("canvas");

    initMap(); // To be moved to backend

    inputHander_init();
    spriteReader_init();
    drawingHandler_init();

    lastFrameTime = Date.now();

    gameLoop();
}


function initMap()
{
    map[0]  = "################";
    map[1]  = "#..............#";
    map[2]  = "#........#######";
    map[3]  = "#..............#";
    map[4]  = "#..............#";
    map[5]  = "#.....##.......#";
    map[6]  = "#.....##.......#";
    map[7]  = "#..............#";
    map[8]  = "#..............#";
    map[9]  = "#..............#";
    map[10] = "######.........#";
    map[11] = "#....#.........#";
    map[12] = "#....#.........#";
    map[13] = "#............###";
    map[14] = "#............###";
    map[15] = "################";
}

function gameLoop()
{
    requestAnimationFrame(gameLoop, canvas);
    
    console.log();

    let currFrameTime = Date.now()
    let deltaTime = currFrameTime - lastFrameTime;
    lastFrameTime = currFrameTime;

    drawingHandler_clearScreen();  // For the text
    //background(0);
    
    inputHandler_updateInput(deltaTime);
    drawingHandler_drawCells();
}