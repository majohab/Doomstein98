// Config
const mouseRotationSpeed = 0.14;
const walkingSpeed = 5;
const rotationSpeed = 0.06;
const playerStartX = 5.0;
const playerStartY = 5.0;
const playerStartAngle = 0.0;

// Runtime variables
let playerX;
let playerY;
let playerAngle;
let pointerLocked;
let lastRecordedMouseX;
let lastMouseX;
let clicked;
let pointerLockedClick; //The click for initialization of pointerLocked should not shoot
let keyStates; // Maybe not how we want to solve this in the final game

function inputHander_init()
{   
    playerX = playerStartX;
    playerY = playerStartY;
    playerAngle = playerStartAngle
    pointerLocked = false;
    pointerLockedClick = false;
    clicked = false;
    keyStates = [];
    
    inputHandler_initMouseEvents();
    inputHandler_initKeyEvents();
    inputHandler_initPointerLock();
}

function inputHandler_initMouseEvents()
{
    lastMouseX = 0;
    
    document.onmousemove = (event) => {
        if (pointerLocked)
            lastRecordedMouseX += event.movementX;
        else
            lastRecordedMouseX = event.pageX;
    }
}

function inputHandler_initKeyEvents()
{
    document.addEventListener('keydown',function(e){
        keyStates[e.keyCode || e.which] = true;
    },true);    
    document.addEventListener('keyup',function(e){
        keyStates[e.keyCode || e.which] = false;
    },true);
    document.addEventListener('click',function (){
        clicked = true;
    })
}

function inputHandler_initPointerLock()
{
    canvas.addEventListener("click", () =>
    {
        canvas.requestPointerLock = canvas.requestPointerLock || canvas.mozRequestPointerLock;
        canvas.requestPointerLock();
        // if mouse is already caught
        if(pointerLocked == false){
            pointerLockedClick = true;
            pointerLocked = true;
        }
    });
}

//function inputHandler_updateInput(deltaTime) // Ultimately to be handled on server-side
//{
//    let dTime = deltaTime / 1000;
//
//    if (lastRecordedMouseX)
//    {
//        let newMouseX = lastRecordedMouseX
//    
//        mouseDeltaX = newMouseX - lastMouseX;
//        playerAngle += mouseDeltaX * mouseRotationSpeed * dTime;
//        lastMouseX = newMouseX;
//    }
//
//    if (keyStates)
//    {
//        if (keyStates[87])
//        {
//            playerX += walkingSpeed * dTime;
//            playerY += walkingSpeed * dTime;
//        }
//        if (keyStates[65])
//        {
//            playerX -= walkingSpeed * dTime;
//            playerY += walkingSpeed * dTime;
//        }
//        if (keyStates[68])
//        {
//            playerX += Math.cos(playerAngle) * walkingSpeed * dTime;
//            playerY -= Math.sin(playerAngle) * walkingSpeed * dTime;
//        }
//        if (keyStates[83])
//        {
//            playerX -= Math.sin(playerAngle) * walkingSpeed * dTime;
//            playerY -= Math.cos(playerAngle) * walkingSpeed * dTime;
//        }
//    }
//}