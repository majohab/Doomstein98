// Config
const cellSize = 2; // Pixels per side of cell
const wallHeight = 1.5;
const depth_cpu = 16.0;
const depth_gpu = 32.0;
const depth_step_cpu = 0.1;
const depth_step_gpu = 0.05;

// Runtime variables
let canvas;
let ctx;
let screenWidth;    // Measured in pixels
let screenHeight;   // Measured in pixels

let gpu;
let gpu_kernel;

let statusBar_Height;

//#region Billboard (UI and Object) config


// Constants

const weapon_pivotX = [21/50, 55/110, 55.5/91]; // pixelOfMid/spriteWidth
const weapon_pivotY = 1;

const healthText_pivotX = 1;
const healthText_pivotY = 1;

const ammoText_pivotX = 1;
const ammoText_pivotY = 1;

const statusBar_pivotX = 0;
const statusBar_pivotY = 0;
const statusBar_startX = 0;

const weaponFrame_pivotX = 0;
const weaponFrame_pivotY = 0;

const waiting_countdown_pivotX = 0.5;
const waiting_countdown_pivotY = 0.5;

const waiting_info_pivotX = 0.5;
const waiting_info_pivotY = 0.5;

const endscreen_pivotX = 0;
const endscreen_pivotY = 0;
const endscreen_startX = 0;
const endscreen_startY = 0;

// Note regarding scale: The rendered size of the object must depend on the sprite's pixel count (width, height)
// We do not want to scale every sprite of an object to the same size
// scale => how much we scale each pixel
const opponent_scaleX = 11;
const opponent_scaleY = opponent_scaleX;
const opponent_startY = 0; // Bottom of corridor
const opponent_pivotY = 0; // Image's reference point is at the bottom

const bullet_scaleX = 5;
const bullet_scaleY = bullet_scaleX;
const bullet_startY = 0.5; // Center of corridor
const bullet_pivotY = 0.5; // Image's reference point is in the middle

const boxes_scaleX = 10;
const boxes_scaleY = boxes_scaleX;
const boxes_startY = 0;
const boxes_pivotY = 0;


// Dependent on screenSize

let weapon_startX;
let weapon_startY;
let weapon_scaleX;
let weapon_scaleY;

let healthText_startX;
let healthText_startY;
let healthText_scaleX;
let healthText_scaleY;

let ammoText_startX;
let ammoText_startY;
let ammoText_scaleX;
let ammoText_scaleY;

let statusBar_startY;
let statusBar_scaleX;
let statusBar_scaleY;

let weaponFrame_startX;
//let weaponFrame_startY; Calculated in drawing function
let weaponFrame_scaleX;
let weaponFrame_scaleY;

let waiting_countdown_startX;
let waiting_countdown_startY;
let waiting_countdown_scaleX;
let waiting_countdown_scaleY;

let waiting_info_startX;
let waiting_info_startY;
let waiting_info_scaleX;
let waiting_info_scaleY;

//let endscreen_scaleX; Calculated in drawing function (depends on the screen we want to draw)
//let endscreen_scaleY;

//#endregion


gameWindowHeight = () => screenHeight - statusBar_Height;

function drawingHandler_init()
{
    screenWidth = 1000;
    screenHeight = 750; // ToDo: Calculate dynamically

    statusBar_Height = screenHeight * 0.15;

    weapon_startX = screenWidth * 0.5;
    weapon_startY = gameWindowHeight();
    weapon_scaleX = weapon_scaleY = screenHeight / 250;

    healthText_startX = screenWidth * 0.43;
    healthText_startY = screenHeight * 0.94;
    healthText_scaleX = healthText_scaleY = screenWidth / 280;

    ammoText_startX = screenWidth * 0.706;
    ammoText_startY = screenHeight * 0.95;
    ammoText_scaleX = ammoText_scaleY = screenWidth / 250;

    statusBar_startY = screenHeight * 0.85;
    statusBar_scaleX = screenWidth / statusBarSprite.width;
    statusBar_scaleY = (screenHeight - statusBar_startY) / statusBarSprite.height;

    weaponFrame_startX = (screenWidth / statusBarSprite.width) * 213;
    weaponFrame_scaleX = statusBar_scaleX;
    weaponFrame_scaleY = statusBar_scaleY;

    waiting_countdown_startX = screenWidth * 0.5;
    waiting_countdown_startY = screenHeight * 0.45;
    waiting_countdown_scaleX = waiting_countdown_scaleY = screenHeight / 100;

    waiting_info_startX = screenWidth * 0.5;
    waiting_info_startY = screenHeight * 0.3;
    waiting_info_scaleX = waiting_info_scaleY = screenHeight / 300;


    canvas = document.createElement('canvas');
    canvas.setAttribute('width', screenWidth);
    canvas.setAttribute('height', screenHeight);//gpu_kernel.canvas;
    document.getElementById("canvas-container").appendChild(canvas);
    ctx = canvas.getContext("webgl2", { premultipliedAlpha: false });

    gpu = new GPU({
        canvas,
        context: ctx
    });

    gpu.addFunction(drawingHandler_draw_gpu_single);

    let gpu_kernel_settings = {
        output: { x: screenWidth, y: screenHeight },
        graphical: true,
        loopMaxIterations: 1000,
        constants:
        {
            screenHeight: screenHeight,
            screenWidth: screenWidth,
            cellSize: cellSize,
            gun_SizeMultiplier: screenHeight / 250,   // ToDo: Usually each weapon should store its own separate reference height additionally, but for now it works fine without.

            fov: fov,
            depth: depth_gpu,
            depth_step_gpu: depth_step_gpu,
            nearClippingPane: 0.5,

            mapWidth: mapWidth,
            mapHeight: mapHeight,

            wallHeight: wallHeight,


            wallSprite_width: wallSprite.width,
            wallSprite_height: wallSprite.height,
            wallSprite_iterations_x: wallSprite.iterations_x,
            wallSprite_iterations_y: wallSprite.iterations_y,

            floorSprite_width: floorSprite.width,
            floorSprite_height: floorSprite.height,
            floorSprite_iterations_x: floorSprite.iterations_x,
            floorSprite_iterations_y: floorSprite.iterations_y,

            ceilingSprite_width: ceilingSprite.width,
            ceilingSprite_height: ceilingSprite.height,
            ceilingSprite_iterations_x: ceilingSprite.iterations_x,
            ceilingSprite_iterations_y: ceilingSprite.iterations_y,
        }
    };
    gpu_kernel = gpu.createKernel(
        function(playerX, playerY, playerAngle, 
            map_numbers,
            wallSprite, floorSprite, ceilingSprite,
            imageArray, imageStartIndezes, imageBounds, imageCount,
            objectArray, objectStartIndezes, objectBounds, objectCount) {
            drawingHandler_draw_gpu_single(playerX, playerY, playerAngle, 
                map_numbers,
                wallSprite, floorSprite, ceilingSprite,
                imageArray, imageStartIndezes, imageBounds, imageCount,
                objectArray, objectStartIndezes, objectBounds, objectCount);
        },
        gpu_kernel_settings
    );
    
    
}

function drawingHandler_initKernel()
{
    let FourBitUnit = [0, 0, 0, 0];
    let EightBitUnit = [0, 0, 0, 0, 0, 0, 0, 0];

    function createEmpty3DArray(width, height, unit)
    {
        let a = [];
        for (let y = 0; y < height; y++)
        {
            a.push([]);
            for (let x = 0; x < width; x++)
                a[y].push(unit);
        }
        return a;
    }

    //#region UI Images

    let imageArray = [];
    let imageStartIndezes = [];
    let imageBounds = [];
    let imageCount = 0;

    // Add biggest expected images
    
    let healthText = getHealthText(200); pushImage(healthText[0].length, healthText.length);
    let ammoText = getAmmoText(200); pushImage(ammoText[0].length, ammoText.length);
    let weaponBounds = shotgunSpriteSet.getBiggestBounds(); pushImage(weaponBounds[0], weaponBounds[1]);
    pushImage(statusBarSprite.width, statusBarSprite.height);
    pushImage(weaponFrameSprite.width, weaponFrameSprite.height);
    let waiting_countdown_text = getWaitingCountdownText(3); pushImage(waiting_countdown_text[0].length, waiting_countdown_text.length);
    let waiting_info_text = getWaitingInfoText(99); pushImage(waiting_info_text[0].length, waiting_info_text.length);
    pushImage(victoryScreenSprite.width, victoryScreenSprite.height); // Note: Victory and Defeat Screen have the same bounds
    function pushImage(width, height) // biggestImage: image with the highest width * height (pixelCount) expected for a particular UI element.
    {
        imageArray.push(createEmpty3DArray(width, height, FourBitUnit));
        imageStartIndezes.push(0);
        imageBounds.push(EightBitUnit);
    }
    imageArray = imageArray.flat(2);

    //#endregion

    //#region 3D Objects

    let objectStartIndezes = []; // [0, 0, 0, ...]
    let objectBounds = []; // array with elements of type [x, y, width, height, scaleX, scaleY, startY, pivotY]

    for (let i = 0; i < maxObjectCount; i++)
    {
        objectStartIndezes.push(0);
        objectBounds.push(EightBitUnit);
    }

    let objectArray = []; // [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], ...]
    pushObjects(fireBulletSpriteSet, max_bullets);
    pushObjects(corpseSpriteSet, max_corpses);
    pushObjects(opponentSpriteSet, max_opponents);
    pushObjects(ammoBoxesSpriteSet, max_boxes);
    function pushObjects(spriteSet, max)
    {
        let spriteBounds = spriteSet.getBiggestBounds();
        let spriteImage = createEmpty3DArray(spriteBounds[0], spriteBounds[1], FourBitUnit)
        for (let i = 0; i < max; i++)
            objectArray.push(spriteImage);
    }

    objectArray = objectArray.flat(2);

    //#endregion

    // Not important (no arrays)
    let weaponFrame_startY = 0;
    let objectCount = 0;

    gpu_kernel(playerX, playerY, playerAngle,
        map_numbers,
        wallSprite.data, floorSprite.data, ceilingSprite.data,
        imageArray, imageStartIndezes, imageBounds, imageCount,
        objectArray, objectStartIndezes, objectBounds, objectCount);
}

//#region  GPU

function drawingHandler_draw()
{

    //#region UI Images

    let imageArray = [];
    let imageStartIndezes = [];
    let imageBounds = [];
    let imageCount = 0;

    function addImage(newImg, startX, startY, pivotX, pivotY, scaleX, scaleY)
    {
        imageStartIndezes.push(imageArray.length);
        imageBounds.push([startX, startY, newImg[0].length, newImg.length, pivotX, pivotY, scaleX, scaleY]);
        imageArray = imageArray.concat(newImg.flat(1)); // Need to flat all sub-objects / -images already at this point, in order to correctly calculate imageStartIndezes
        imageCount++;
    }

    addImage(statusBarSprite.data, statusBar_startX, statusBar_startY, statusBar_pivotX, statusBar_pivotY, statusBar_scaleX, statusBar_scaleY);
    addImage(getHealthText(), healthText_startX, healthText_startY, healthText_pivotX, healthText_pivotY, healthText_scaleX, healthText_scaleY);
    addImage(getAmmoText(), ammoText_startX, ammoText_startY, ammoText_pivotX, ammoText_pivotY, ammoText_scaleX, ammoText_scaleY);    

    let weaponFrame_startY = statusBar_startY + (2 + currWeapon * 12) * statusBar_scaleY;
    addImage(weaponFrameSprite.data, weaponFrame_startX, weaponFrame_startY, weaponFrame_pivotX, weaponFrame_pivotY, weaponFrame_scaleX, weaponFrame_scaleY);

    let weaponToUse = currWeapon == 0 ? handgunSpriteSet : currWeapon == 1 ? chaingunSpriteSet : shotgunSpriteSet;
    let weaponImage;
    if (weaponAnimTime == -1)
    {
        weaponImage = weaponToUse.getSprite('Idle');        
    }
    else
    {
        let t = weaponAnimTime / weaponImageAnimationTime;
        t = 1 - t; // [0, 1): Animation; 1: Still
        weaponImage = weaponToUse.getAnimationSprite(t, 'Shoot');
    }

    addImage(weaponImage, weapon_startX, weapon_startY, weapon_pivotX[currWeapon], weapon_pivotY, weapon_scaleX, weapon_scaleY)

    
    if (gameState == 0)
    {
        addImage(getWaitingCountdownText(), waiting_countdown_startX, waiting_countdown_startY, waiting_countdown_pivotX, waiting_countdown_pivotY, waiting_countdown_scaleX, waiting_countdown_scaleY);
        addImage(getWaitingInfoText(), waiting_info_startX, waiting_info_startY, waiting_info_pivotX, waiting_info_pivotY, waiting_info_scaleX, waiting_info_scaleY);
    }
    else if (gameState == 3)
    {
        addImage(victoryScreenSprite.data, endscreen_startX, endscreen_startY, endscreen_pivotX, endscreen_pivotY, screenWidth / victoryScreenSprite.width, screenHeight / victoryScreenSprite.height);
    }
    else if (gameState == 4)
    {
        addImage(defeatScreenSprite.data, endscreen_startX, endscreen_startY, endscreen_pivotX, endscreen_pivotY, screenWidth / defeatScreenSprite.width, screenHeight / defeatScreenSprite.height);
    }

    //#endregion

    //#region 3D Objects

    let objectArray = [];
    let objectStartIndezes = [];
    let objectBounds = [];
    let objectCount = 0;

    function addObjects(maxCount, rec_objects, scaleX, scaleY, startY, pivotY, presentObject_Function)
    {
        for (let i = 0; i < maxCount; i++)
        {
            let newObject;

            if (i < rec_objects.length)
            {
                let x = rec_objects[i][x_coordinate_key];
                let y = rec_objects[i][y_coordinate_key];

                newObject = presentObject_Function(rec_objects[i]);
                
                if (typeof newObject != undefined && newObject != null)
                {
                    objectStartIndezes.push(objectArray.length);
                    objectBounds.push([x, y, newObject[0].length, newObject.length, scaleX, scaleY, startY, pivotY]);
                    objectArray = objectArray.concat(newObject.flat(1));
                    objectCount++;
                }
                else
                {
                    console.error('Something went wrong, please check the presentObject_Functions');
                }
            }
        }
    }

    function getEightDirSprite(object, animTime, spriteSet, spriteSet_stillName = 'Idle', spriteSet_animationName = 'Walk')
    {
        function getDeltaBetweenAngles(a, b)
        {
            let delta = a - b;
            delta += (delta > PI) ? -(2*PI) : (delta < -PI) ? (2*PI) : 0;
            return delta
        }

        const PI = Math.PI;

        let vecX = object[x_coordinate_key] - playerX;
        let vecY = object[y_coordinate_key] - playerY;
        let angleToOpponent = Math.atan2(vecX, vecY); // Yeah usually it is (y, x), but it only works like this (maybe there is (x, y) in the backend?)

        // delta is the angle which to opponent looks in relative to the vector between opponent and self
        let delta = getDeltaBetweenAngles(object[direction_view_key], angleToOpponent);

        let spriteDir;
        if (delta > PI * (7 / 8) || delta <= -PI * (7 / 8))
            spriteDir = 'S';
        else if (delta > PI * (5 / 8))
            spriteDir = 'SE';
        else if (delta > PI * (3 / 8))
            spriteDir = 'E';
        else if (delta > PI * (1 / 8))
            spriteDir = 'NE';
        else if (delta > -PI * (1 / 8))
            spriteDir = 'N';
        else if (delta > -PI * (3 / 8))
            spriteDir = 'NW';
        else if (delta > -PI * (5 / 8))
            spriteDir = 'W'
        else if (delta > -PI * (7 / 8))
            spriteDir = 'SW'
        else
        {
            spriteDir = 'S';
            console.error('Something went wrong');
        }

        let animationName;
        let t = object[move_animation_key];

        if (t == -1)
        {
            animationName = spriteSet_stillName;
        }
        else
        {
            animationName = spriteSet_animationName;

            t /= animTime;

            if (t > 1)
                console.error('t > 1: This should never happen! The parameter animTime is probably incorrect.'); // It doesn't matter too much though, getAnimationSprite handles this case as well

            if (object[direction_move_key])
            {
                // Check whether object moves in opposite direction (angle between movement and looking > 90) (currently only applicable for opponents)
                let movementDelta = getDeltaBetweenAngles(object[direction_view_key], object[direction_move_key]);
                if (movementDelta > PI*0.5 || movementDelta < -PI*0.5)
                    t = 1 - t;
            }
        }
        
        return spriteSet.getAnimationSprite(t, animationName + '_' + spriteDir);

    }

    addObjects(max_opponents, rec_opponents, opponent_scaleX, opponent_scaleY, opponent_startY, opponent_pivotY, (object) => getEightDirSprite(object, playerWalkingAnimationTime, opponentSpriteSet));
    addObjects(max_bullets, rec_bullets, bullet_scaleX, bullet_scaleY, bullet_startY, bullet_pivotY, (object) => getEightDirSprite(object, bulletFlyingAnimationTime, fireBulletSpriteSet, 'Idle', 'Fly'));
    addObjects(max_corpses, rec_corpses, opponent_scaleX, opponent_scaleY, opponent_startY, opponent_pivotY, (object) =>
    {
        let corpse;
        let t = object[duration_key];
        let totalTime = corpseTotalAnimationTime;
        let animTime = 20;
        t -= totalTime - animTime;
        if (t > 0)
        {
            t = t / animTime;
            t = 1 - t;
            corpse = corpseSpriteSet.getAnimationSprite(t, 'Explode');
        }
        else
        {
            corpse = corpseSpriteSet.getSprite('Idle');
        }
        return corpse;
        
    });
    addObjects(max_boxes, rec_boxes, boxes_scaleX, boxes_scaleY, boxes_startY, boxes_pivotY, (object) => 
    {
        return ammoBoxesSpriteSet.getSprite(object[name_key] == 'Pistol' ? 0 : object[name_key] == 'Chaingun' ? 1 : 2);
    });

    if (objectCount == 0)
    {
        objectArray.push(0);
        objectStartIndezes.push(0);
        objectBounds.push(0);
    }

    //#endregion

    gpu_kernel(playerX, playerY, playerAngle,
        map_numbers,
        wallSprite.data, floorSprite.data, ceilingSprite.data,
        imageArray, imageStartIndezes, imageBounds, imageCount,
        objectArray, objectStartIndezes, objectBounds, objectCount);
}

function drawingHandler_draw_gpu_single(playerX, playerY, playerAngle,      // Coordinates and Angle
    map_numbers,                                                            // Map
    wallSprite, floorSprite, ceilingSprite,                                 // World Sprites                                              
    imageArray, imageStartIndezes, imageBounds, imageCount,
    objectArray, objectStartIndezes, objectBounds, objectCount)                                                     
{
    //#region Init

    let screenWidth = this.constants.screenWidth;
    let screenHeight = this.constants.screenHeight;
    //this.constants.statusBarSprite_height * (screenWidth / this.constants.statusBarSprite_width); This would force a correct aspect-ratio

    // Read values (y must be inverted, we're looking from top to bottom this time)
    let x = this.thread.x;
    let y = screenHeight-this.thread.y;
    // Round all pixels within cell to top-left of the cell
    x = Math.floor(x / this.constants.cellSize) * this.constants.cellSize;
    y = Math.round(y / this.constants.cellSize) * this.constants.cellSize;
    // Center of the cell
    x += (this.constants.cellSize - 1) * 0.5;
    y += (this.constants.cellSize - 1) * 0.5;
        
    let r = 0;
    let g = 0;
    let b = 0;

    let depth = this.constants.depth;
    let depthBuffer = depth;

    //#endregion

    //#region UI-Elements
    {
        for (let image = 0; image < imageCount; image++)
        {
            let posX = imageBounds[image][0];
            let posY = imageBounds[image][1];
            let width = imageBounds[image][2];
            let height = imageBounds[image][3];
            let pivotX = imageBounds[image][4]; // [0, 1]: from left to right
            let pivotY = imageBounds[image][5]; // [0, 1]: from top to bottom
            let scaleX = imageBounds[image][6];
            let scaleY = imageBounds[image][7];

            // ToMaybeDo: Calculate in cpu code
            let startX = posX - pivotX * width * scaleX;
            let startY = posY - pivotY * height * scaleY;
            let endX = startX + (width * scaleX);
            let endY = startY + (height * scaleY);

            
            if (x >= startX && x < endX && y >= startY && y < endY)
            {
                let pix_x = Math.floor((x - startX) / scaleX);
                let pix_y = Math.floor((y - startY) / scaleY);

                let offset = imageStartIndezes[image];
                let pixelIndex = offset + pix_y * width + pix_x;

                if (imageArray[pixelIndex][3] > 0)
                {
                    r = imageArray[pixelIndex][0]
                    g = imageArray[pixelIndex][1]
                    b = imageArray[pixelIndex][2]
                
                    depthBuffer = 0;
                }
            }   
        }     
    }
    //#endregion

    //#region 3D Ray-Casting

    if (depthBuffer > 0)
    {
        //#region Wall, Ceiling, Floor

        let fov = this.constants.fov;
        let mapWidth = this.constants.mapWidth;
        let mapHeight = this.constants.mapHeight;
        let wallHeight = this.constants.wallHeight;

        let rayAngle = (playerAngle - fov * 0.5) + (x / screenWidth) * fov;

        let distanceToWall = 0;
        let hitWall = false;

        // eye: Unit-vector for ray in player-space
        let eyeX = Math.sin(rayAngle);
        let eyeY = Math.cos(rayAngle);

        let sampleX_wall = 0;

        while (!hitWall && distanceToWall < depth)
        {      
            distanceToWall += this.constants.depth_step_gpu;

            let testX = Math.floor(playerX + eyeX * distanceToWall);
            let testY = Math.floor(playerY + eyeY * distanceToWall);

            if (testX < 0 || testX >= mapWidth || testY < 0 || testY >= mapHeight) // Out of map bounds
            {
                hitWall = true;
                distanceToWall = depth;
            }
            else if (map_numbers[testY * mapWidth + testX] == 35)
            {
                hitWall = true;
            
                let blockMidX = testX + 0.5;
                let blockMidY = testY + 0.5;
            
                let testPointX = playerX + eyeX * distanceToWall;
                let testPointY = playerY + eyeY * distanceToWall;
            
                let testAngle = Math.atan2((testPointY - blockMidY), (testPointX - blockMidX));
            
                if (testAngle >= -Math.PI * 0.25 && testAngle < Math.PI * 0.25)
                    sampleX_wall = testPointY - testY;
                if (testAngle >= Math.PI * 0.25 && testAngle < Math.PI * 0.75)
                    sampleX_wall = testPointX - testX;
                if (testAngle < -Math.PI * 0.25 && testAngle >= -Math.PI * 0.75)
                    sampleX_wall = testPointX - testX;
                if (testAngle >= Math.PI * 0.75 || testAngle < -Math.PI * 0.75)
                    sampleX_wall = testPointY - testY;
            }
        }

        let ceiling = ((screenHeight * 0.5) - ((screenHeight / distanceToWall)) * (screenHeight / screenWidth) * wallHeight);
        let floor = screenHeight - ceiling;

        let sampleX = 0;
        let sampleY = 0;
        let spriteIndex = 0;

        if (y >= ceiling && y <= floor) // Wall
        {
            sampleX = sampleX_wall;
            let sampleY_percent = (y - ceiling) / (floor - ceiling); // percent-value between floor and ceiling
            sampleY = sampleY_percent * wallHeight;

            spriteIndex = 0;
        }
        else // Floor or Ceiling
        {
            // Current y position compared to the center of the screen (the horizon)
            let p = y - screenHeight * 0.5;

            // Vertical position of the camera.
            let posZ = 0.5 * screenHeight;

            // Horizontal distance from the camera to the floor for the current row.
            // 0.5 is the z position exactly in the middle between floor and ceiling.
            let rowDistance = posZ / p;

            if (y < ceiling) // Ceiling / Sky
            {
            
                let constant = 0.66;

                sampleX = rowDistance * eyeX
                    - playerX * (constant / wallHeight); // Comment this out to render as sky
                sampleX -= Math.floor(sampleX);
                sampleY = rowDistance * eyeY
                    - playerY * (constant / wallHeight); // Comment this out to render as sky
                sampleY -= Math.floor(sampleY);
            
                //sprite = ceilingSprite;
            
                spriteIndex = 2;
            }
            else // Floor
            {
                // Zero idea why this constant... It was a late sunday evening and this number just did the trick ^^'
                // It seems to have a connection with screenHeight and screenWidth though.
                // Lower: floor moves in direction of player. Higher: floor moves in opposite direction
                let constant = 0.66;

                sampleX = rowDistance * eyeX + playerX * (constant / wallHeight);
                sampleX -= Math.floor(sampleX);
                sampleY = rowDistance * eyeY + playerY * (constant / wallHeight);
                sampleY -= Math.floor(sampleY);
            
                spriteIndex = 1
            }

            //ctx.fillStyle = "rgb(" + sampleY * 255 + "," + sampleY * 255  + "," + sampleY * 255   + ")";
        }

        let spriteWidth = 0;
        let spriteHeight = 0;
        let iterations_x = 0;
        let iterations_y = 0;
        if (spriteIndex == 0)
        {
            spriteWidth  = this.constants.wallSprite_width;
            spriteHeight = this.constants.wallSprite_height;
            iterations_x = this.constants.wallSprite_iterations_x;
            iterations_y = this.constants.wallSprite_iterations_y;
        }
        else if (spriteIndex == 1)
        {
            spriteWidth  = this.constants.floorSprite_width;
            spriteHeight = this.constants.floorSprite_height;
            iterations_x = this.constants.floorSprite_iterations_x;
            iterations_y = this.constants.floorSprite_iterations_y;
        }
        else if (spriteIndex == 2)
        {
            spriteWidth  = this.constants.ceilingSprite_width;
            spriteHeight = this.constants.ceilingSprite_height;
            iterations_x = this.constants.ceilingSprite_iterations_x;
            iterations_y = this.constants.ceilingSprite_iterations_y;
        }

        let pix_x = Math.floor(sampleX * spriteWidth * iterations_x) % spriteWidth;
        let pix_y = Math.floor(sampleY * spriteHeight * iterations_y) % spriteHeight;

        pix_y = spriteHeight - pix_y - 1;

        r = spriteIndex == 0 ? wallSprite[pix_y][pix_x][0] : spriteIndex == 1 ? floorSprite[pix_y][pix_x][0] : ceilingSprite[pix_y][pix_x][0];
        g = spriteIndex == 0 ? wallSprite[pix_y][pix_x][1] : spriteIndex == 1 ? floorSprite[pix_y][pix_x][1] : ceilingSprite[pix_y][pix_x][1];
        b = spriteIndex == 0 ? wallSprite[pix_y][pix_x][2] : spriteIndex == 1 ? floorSprite[pix_y][pix_x][2] : ceilingSprite[pix_y][pix_x][2];
        
        depthBuffer = distanceToWall;

        //#endregion

        //#region Objects

        //#endregion

        {
            for (let object = 0; object < objectCount; object++) // First element is 0
            {
                let objX = objectBounds[object][0];
                let objY = objectBounds[object][1];
                let spriteWidth = objectBounds[object][2];
                let spriteHeight = objectBounds[object][3];
                let scaleX = objectBounds[object][4];
                let scaleY = objectBounds[object][5];
                let startY = objectBounds[object][6]; // [0, 1]
                let pivotY = objectBounds[object][7]; // [0, 1]

                let vecX = objX - playerX;
                let vecY = objY - playerY;
                let dstFromPlayer = Math.sqrt(vecX*vecX + vecY*vecY);

                let forwardX = Math.sin(playerAngle); let forwardY = Math.cos(playerAngle);

                let objAngle = Math.atan2(forwardY, forwardX) - Math.atan2(vecY, vecX);

                let inFrontOfPlayer = (forwardX * vecX + forwardY * vecY) > 0;

                if (inFrontOfPlayer &&
                    dstFromPlayer >= this.constants.nearClippingPane &&
                    dstFromPlayer < depth &&
                    dstFromPlayer < depthBuffer)
                {
                    //((screenHeight * 0.5) - ((screenHeight / distanceToWall)) * (screenHeight / screenWidth) * wallHeight)
                    let corridorCeiling = ((screenHeight * 0.5) - ((screenHeight / dstFromPlayer)) * (screenHeight / screenWidth) * wallHeight);
                    let corridorFloor = screenHeight - corridorCeiling;

                    //corridorCeiling = ceiling; Use those lines for funny effects ^^
                    //corridorFloor = floor;

                    let corridorHeight = corridorFloor - corridorCeiling;

                    // Note that dividing by screenHeight isn't really necessary, it just makes the values easier to work with
                    // as the last part of the equation is now in range [0, 1]
                    let objHeight = (spriteHeight * scaleX) * (corridorHeight / screenHeight);

                    let objRatio = spriteWidth / spriteHeight;
                    let objWidth = objHeight * objRatio;
                    let middleOfObject_x = (0.5 * (objAngle / (fov * 0.5)) + 0.5) * screenWidth; // middle pixel of object. Range [0, screenWidth] (I think, lol)

                    // Absolutely zero idea what the following does and why the f*ck it works... It just works okay?! It just works... for now...
                    // Also, note that this only seems to work for fov = PI / 3, we probably need to adapt that sh*t calculation for other fovs.
                    if (middleOfObject_x < 0 + objWidth * 0.5) middleOfObject_x += screenWidth * 3;
                    if (middleOfObject_x > screenWidth * 3 - objWidth * 0.5) middleOfObject_x -= screenWidth * 3;

                    let objMinX = middleOfObject_x - objWidth * 0.5;
                    let objMaxX = middleOfObject_x + objWidth * 0.5;

                    let objMinY = screenHeight * 0.5 - objHeight * 0.5; // screenHeight * 0.5: Start calculation in the center of the screen
                    let objMaxY = screenHeight * 0.5 + objHeight * 0.5;

                    let yOffset = 0;
                    yOffset += ((startY - 0.5) * corridorHeight);
                    yOffset += ((0.5 - pivotY) * objHeight);
                    objMinY -= yOffset; objMaxY -= yOffset;

                    if (x >= objMinX && x <= objMaxX && y >= objMinY && y <= objMaxY)
                    {
                        let pix_x = Math.floor(((x - objMinX) / objWidth) * spriteWidth);
                        let pix_y = Math.floor(((objMaxY - y) / objHeight) * spriteHeight);

                        let offset = objectStartIndezes[object];
                        let pixelIndex = offset + pix_y * spriteWidth + pix_x;

                        if (objectArray[pixelIndex][3] > 0)  // If not transparent
                        {
                            r = objectArray[pixelIndex][0]; //r = corpses[offset + pix_y][pix_x][0];
                            g = objectArray[pixelIndex][1]; //g = corpses[offset + pix_y][pix_x][1];
                            b = objectArray[pixelIndex][2]; //b = corpses[offset + pix_y][pix_x][2];
                            depthBuffer = dstFromPlayer;
                        }
                    }
                }
            }
        }
    }

    //#endregion
            
    this.color(r / 255, g / 255, b / 255)
}

//#endregion