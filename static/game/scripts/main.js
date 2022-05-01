// Config
const fov = Math.PI / 3;
const max_corpses = 5;
const max_opponents = 5;
const max_bullets = 100;

// Runtime variables
let lastFrameTime;
let mapString;
let map_numbers;
let mapWidth;    // 87
let mapHeight;   // 38

// Received from backend each frame
let playerX;
let playerY;
let playerAngle;
let opponents;
let currWeapon;
let health;
let ammo;               // ToRefactor: Merge a padded sprite and its bounds into a new class
let weaponAnimTime;

async function init()
{    
    socketHandler_init();

    await spriteReader_init();
    
    initRuntimeVariables();

    await initMap_Numbers();

    drawingHandler_init(); // Needs to wait for initRuntimeVariables();

    inputHander_init(); // Needs to wait for drawingHandler_init()

    gameLoop();
}

function initRuntimeVariables()
{
    ammo = 200;
    health = 200;
    currWeapon = 2;
    weaponAnimTime = -1;

    //#region Init Textures with their biggest size
    let healthText = getHealthText();
    healthTextBounds_sizeX = healthText[0].length;
    healthTextBounds_sizeY = healthText.length;
    healthTextPaddingConfig = new PaddingConfig(healthText[0].length, healthText.length, -1, 0)

    let ammoText = getAmmoText();
    ammoTextBounds_sizeX = ammoText[0].length;
    ammoTextBounds_sizeY = ammoText.length;
    ammoTextPaddingConfig = new PaddingConfig(ammoTextBounds_sizeX, ammoTextBounds_sizeY, -1, 0);

    //#endregion

    lastFrameTime = Date.now();
}


function getHealthText()
{
    return font.getTextImg(health.toString()/*.padStart(3, '0')*/ + '%');
}

function getAmmoText()
{
    return font.getTextImg(ammo.toString()/*.padStart(3, '0')*/);
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