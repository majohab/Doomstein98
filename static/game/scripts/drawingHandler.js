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

//#region Image (UI and Object) config


// Constants

const weapon_pivotX = [21/52, 55/110, 55.5/91]; // pixelOfMid/spriteWidth
const weapon_pivotY = 1;

const healthText_pivotX = 1;
const healthText_pivotY = 1;

const ammoText_pivotX = 1;
const ammoText_pivotY = 1;

// We call it PIXELscale, as it the rendered size of the object must depend on the sprite's pixel count (width, height)
// We do not want to scale every sprite of an object to the same size
// pixelScale => how we scale each pixel
const opponent_pixelScale = 11;
const opponent_startY = 0; // Bottom of corridor
const opponent_pivotY = 0; // Image's reference point is at the bottom

const bullet_pixelScale = 5;
const bullet_startY = 0.5; // Center of corridor
const bullet_pivotY = 0.5; // Image's reference point is in the middle

const boxes_pixelScale = 10;
const boxes_startY = 0;
const boxes_pivotY = 0;


// Dependent on screenSize

let weapon_startX;
let weapon_startY;
let weapon_scale;

let healthText_startX;
let healthText_startY;
let healthText_scale;

let ammoText_startX;
let ammoText_startY;
let ammoText_scale;

//#endregion


gameWindowHeight = () => screenHeight - statusBar_Height;

function drawingHandler_init()
{
    screenWidth = 1000;
    screenHeight = 750; // ToDo: Calculate dynamically

    statusBar_Height = screenHeight * 0.15;

    weapon_startX = screenWidth * 0.5;
    weapon_startY = gameWindowHeight();
    weapon_scale = screenHeight / 250;

    healthText_startX = screenWidth * 0.43;
    healthText_startY = screenHeight * 0.94;
    healthText_scale = screenWidth / 280;

    ammoText_startX = screenWidth * 0.706;
    ammoText_startY = screenHeight * 0.95;
    ammoText_scale = screenWidth / 250;

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
            statusBar_Height: statusBar_Height,
            weaponFrame_startX: (screenWidth / statusBarSprite.width) * 213,
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

            statusBarSprite_width: statusBarSprite.width,
            statusBarSprite_height: statusBarSprite.height,

            weaponFrameSprite_width: weaponFrameSprite.width,
            weaponFrameSprite_height: weaponFrameSprite.height
        }
    };
    gpu_kernel = gpu.createKernel(
        function(playerX, playerY, playerAngle, 
            map_numbers,
            wallSprite, floorSprite, ceilingSprite, statusBarSprite, weaponFrameSprite,
            imageArray, imageStartIndezes, imageBounds, imageCount,
            weaponFrame_startY,
            objectArray, objectStartIndezes, objectBounds, objectCount) {
            drawingHandler_draw_gpu_single(playerX, playerY, playerAngle, 
                map_numbers,
                wallSprite, floorSprite, ceilingSprite, statusBarSprite, weaponFrameSprite,
                imageArray, imageStartIndezes, imageBounds, imageCount,
                weaponFrame_startY,
                objectArray, objectStartIndezes, objectBounds, objectCount);
        },
        gpu_kernel_settings
    );
    
    
}

function drawingHandler_initKernel()
{
    let FourBitUnit = [0, 0, 0, 0];
    let SevenBitUnit = [0, 0, 0, 0, 0, 0, 0];

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
    function pushImage(width, height) // biggestImage: image with the highest width * height (pixelCount) expected for a particular UI element.
    {
        imageArray.push(createEmpty3DArray(width, height, FourBitUnit));
        imageStartIndezes.push(0);
        imageBounds.push(SevenBitUnit);
    }
    imageArray = imageArray.flat(2);

    //#endregion

    //#region 3D Objects

    let objectStartIndezes = []; // [0, 0, 0, ...]
    let objectBounds = []; // array with elements of type [x, y, width, height, pixelScale, startY, pivotY]

    for (let i = 0; i < maxObjectCount; i++)
    {
        objectStartIndezes.push(0);
        objectBounds.push(SevenBitUnit);
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
        wallSprite.data, floorSprite.data, ceilingSprite.data, statusBarSprite.data, weaponFrameSprite.data,
        imageArray, imageStartIndezes, imageBounds, imageCount,
        weaponFrame_startY,
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

    function addImage(newImg, startX, startY, pivotX, pivotY, scale)
    {
        imageStartIndezes.push(imageArray.length);
        imageBounds.push([startX, startY, newImg[0].length, newImg.length, pivotX, pivotY, scale]);
        imageArray = imageArray.concat(newImg.flat(1)); // Need to flat all sub-objects / -images already at this point, in order to correctly calculate imageStartIndezes
        imageCount++;
    }

    addImage(getHealthText(), healthText_startX, healthText_startY, healthText_pivotX, healthText_pivotY, healthText_scale);
    addImage(getAmmoText(), ammoText_startX, ammoText_startY, ammoText_pivotX, ammoText_pivotY, ammoText_scale);


    let weaponFrame_startY = 2 + currWeapon * 12;

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

    addImage(weaponImage, weapon_startX, weapon_startY, weapon_pivotX[currWeapon], weapon_pivotY, weapon_scale)

    //#endregion

    //#region 3D Objects

    let objectArray = [];
    let objectStartIndezes = [];
    let objectBounds = [];
    let objectCount = 0;

    function addObjects(maxCount, rec_objects, pixelScale, startY, pivotY, presentObject_Function)
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
                    objectBounds.push([x, y, newObject[0].length, newObject.length, pixelScale, startY, pivotY]);
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

    addObjects(max_opponents, rec_opponents, opponent_pixelScale, opponent_startY, opponent_pivotY, (object) => getEightDirSprite(object, playerWalkingAnimationTime, opponentSpriteSet));
    addObjects(max_bullets, rec_bullets, bullet_pixelScale, bullet_startY, bullet_pivotY, (object) => getEightDirSprite(object, bulletFlyingAnimationTime, fireBulletSpriteSet, 'Idle', 'Fly'));
    addObjects(max_corpses, rec_corpses, opponent_pixelScale, opponent_startY, opponent_pivotY, (object) =>
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
    addObjects(max_boxes, rec_boxes, boxes_pixelScale, boxes_startY, boxes_pivotY, (object) => 
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
        wallSprite.data, floorSprite.data, ceilingSprite.data, statusBarSprite.data, weaponFrameSprite.data,
        imageArray, imageStartIndezes, imageBounds, imageCount,
        weaponFrame_startY,
        objectArray, objectStartIndezes, objectBounds, objectCount);
}

function drawingHandler_draw_gpu_single(playerX, playerY, playerAngle,      // Coordinates and Angle
    map_numbers,                                                            // Map
    wallSprite, floorSprite, ceilingSprite, statusBarSprite, weaponFrameSprite,    // World Sprites                                              
    imageArray, imageStartIndezes, imageBounds, imageCount,
    weaponFrame_startY,                 // Status-Bar-Weapon-Frame
    objectArray, objectStartIndezes, objectBounds, objectCount)                                                     
{
    //#region Init

    let screenWidth = this.constants.screenWidth;
    let screenHeight = this.constants.screenHeight;
    let statusBarHeight = this.constants.statusBar_Height;
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

    let gameWindowHeight = screenHeight - statusBarHeight; // Measured in pixels
        // Somehow this still prints a 1px line when statusBar_Height == 0,
        // so it seems that the bottom row has y = screenHeight + 1
        // -> We'll ignore this for now
        
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
            let scale = imageBounds[image][6];

            // ToMaybeDo: Calculate in cpu code
            let startX = posX - pivotX * width * scale;
            let startY = posY - pivotY * height * scale;
            let endX = startX + (width * scale);
            let endY = startY + (height * scale);

            
            if (x >= startX && x < endX && y >= startY && y < endY)
            {
                let pix_x = Math.floor((x - startX) / scale);
                let pix_y = Math.floor((y - startY) / scale);

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

    //#region Status-Bar
    if (depthBuffer > 0 && y > gameWindowHeight)
    {
        let localY = y - gameWindowHeight;

        let spriteWidth = this.constants.statusBarSprite_width;
        let spriteHeight = this.constants.statusBarSprite_height;

        let pix_x = Math.floor((x / screenWidth) * spriteWidth);
        let pix_y = Math.floor((localY / statusBarHeight) * spriteHeight);
        pix_y = spriteHeight - pix_y - 1;

        if (statusBarSprite[pix_y][pix_x][3] > 0)
        {
            r = statusBarSprite[pix_y][pix_x][0];
            g = statusBarSprite[pix_y][pix_x][1];
            b = statusBarSprite[pix_y][pix_x][2];

            depthBuffer = 0;
        }

        //#region Weapon-Frame

        {
            let statusBarScale_width = screenWidth / spriteWidth;
            let statusBarScale_height = statusBarHeight / spriteHeight;

            let startX = this.constants.weaponFrame_startX;
            let endX = startX + this.constants.weaponFrameSprite_width * statusBarScale_width;
            let startY = gameWindowHeight + (weaponFrame_startY) * statusBarScale_height;
            let endY = startY + this.constants.weaponFrameSprite_height * statusBarScale_height;

            if (x >= startX && x < endX && y >= startY && y < endY)
            {
                let pix_x = Math.floor((x - startX) / statusBarScale_width);
                let pix_y = Math.floor((y - startY) / statusBarScale_height);

                if (weaponFrameSprite[pix_y][pix_x][3] > 0)
                {
                    r = weaponFrameSprite[pix_y][pix_x][0];
                    g = weaponFrameSprite[pix_y][pix_x][1];
                    b = weaponFrameSprite[pix_y][pix_x][2];
                        
                    depthBuffer = 0;
                }
            }
        }
        //#endregion
        
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
                let pixelScale = objectBounds[object][4];
                let startY = objectBounds[object][5]; // [0, 1]
                let pivotY = objectBounds[object][6]; // [0, 1]

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
                    let objHeight = (spriteHeight * pixelScale) * (corridorHeight / screenHeight);

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