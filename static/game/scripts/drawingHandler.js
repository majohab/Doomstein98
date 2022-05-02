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

let buffer;

let gpu;
let gpu_kernel;
let gpu_kernel_settings;

let healthTextBounds_startX;
let healthTextBounds_startY;
let healthTextBounds_sizeX;
let healthTextBounds_sizeY;
let healthTextBounds_scale;
let healthTextPaddingConfig;

let ammoTextBounds_startX;
let ammoTextBounds_startY;
let ammoTextBounds_sizeX;
let ammoTextBounds_sizeY;
let ammoTextBounds_scale;
let ammoTextPaddingConfig;

let weaponImageBounds;

function drawingHandler_init()
{
    screenWidth = 1000;
    screenHeight = 750; // ToDo: Calculate dynamically

    healthTextBounds_startX = screenWidth * (285 / 1200);
    healthTextBounds_startY = screenHeight - screenHeight * (115 / 900);
    healthTextBounds_scale = screenWidth / 280;

    ammoTextBounds_startX = screenWidth * (645 / 1200);
    ammoTextBounds_startY = screenHeight - screenHeight * (120 / 900);
    ammoTextBounds_scale = screenWidth / 240;

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

    gpu_kernel_settings = {
        output: { x: screenWidth, y: screenHeight },
        graphical: true,
        loopMaxIterations: 1000,
        constants:
        {
            screenHeight: screenHeight,
            screenWidth: screenWidth,
            cellSize: cellSize,
            statusBar_Height: screenHeight * 0.15,
            weaponFrame_startX: (screenWidth / statusBarSprite.width) * 213,
            gun_Height: screenHeight / 3,   // ToDo: Usually each weapon should store its own separate reference height additionally, but for now it works fine without.

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
            weaponFrameSprite_height: weaponFrameSprite.height,


            healthTextBounds_startX: healthTextBounds_startX,
            healthTextBounds_startY: healthTextBounds_startY,
            healthTextBounds_sizeX: healthTextBounds_sizeX,
            healthTextBounds_sizeY: healthTextBounds_sizeY,
            healthTextBounds_scale: healthTextBounds_scale,

            ammoTextBounds_startX: ammoTextBounds_startX,
            ammoTextBounds_startY: ammoTextBounds_startY,
            ammoTextBounds_sizeX: ammoTextBounds_sizeX,
            ammoTextBounds_sizeY: ammoTextBounds_sizeY,
            ammoTextBounds_scale: ammoTextBounds_scale
        }
    };
    gpu_kernel = gpu.createKernel(
        function(playerX, playerY, playerAngle, 
            map_numbers,
            wallSprite, floorSprite, ceilingSprite, statusBarSprite, weaponFrameSprite,
            weaponImage, weaponImageBounds,
            healthText, bulletsText,
            weaponFrame_startY,
            objectArray, objectStartIndezes, objectBounds, objectCount) {
            drawingHandler_draw_gpu_single(playerX, playerY, playerAngle, 
                map_numbers,
                wallSprite, floorSprite, ceilingSprite, statusBarSprite, weaponFrameSprite,
                weaponImage, weaponImageBounds,
                healthText, bulletsText,
                weaponFrame_startY,
                objectArray, objectStartIndezes, objectBounds, objectCount);
        },
        gpu_kernel_settings
    );
    
    
}

function drawingHandler_initKernel()
{
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


    let FourBitUnit = [0, 0, 0, 0];

    let weaponImageBounds = shotgunSprite.getBiggestBounds();
    let weaponImage = createEmpty3DArray(weaponImageBounds[0], weaponImageBounds[1], FourBitUnit);

    let healthText = createEmpty3DArray(healthTextBounds_sizeX, healthTextBounds_sizeY, FourBitUnit);
    let ammoText = createEmpty3DArray(ammoTextBounds_sizeX, ammoTextBounds_sizeY, FourBitUnit);


    let objectStartIndezes = [];
    let objectBounds = [];

    for (let i = 0; i < max_opponents * max_bullets * max_corpses; i++)
    {
        objectStartIndezes.push(0);
        objectBounds.push([0, 0, 0, 0]);
    }

    let objectArray = [];
    pushObjects(fireBulletSprite, max_bullets);
    pushObjects(corpseSprite, max_corpses);
    pushObjects(playerSprite, max_opponents);
    function pushObjects(spriteSet, max)
    {
        let spriteBounds = spriteSet.getBiggestBounds();
        let spriteImage = createEmpty3DArray(spriteBounds[0], spriteBounds[1], FourBitUnit)
        for (let i = 0; i < max; i++)
            objectArray.push(spriteImage);
    }

    objectArray = objectArray.flat(2);


    // Not important (no arrays)
    let weaponFrame_startY = 0;
    let objectCount = 0;

    buffer = gpu_kernel(playerX, playerY, playerAngle,
        map_numbers,
        wallSprite.data, floorSprite.data, ceilingSprite.data, statusBarSprite.data, weaponFrameSprite.data,
        weaponImage, weaponImageBounds,
        healthText, ammoText,
        weaponFrame_startY,
        objectArray, objectStartIndezes, objectBounds, objectCount);
}

//#region  GPU

function drawingHandler_draw()
{

    //#region UI

    let healthText = getHealthText();
    healthText = padSprite(healthText, healthTextPaddingConfig);

    
    let ammoText = getAmmoText();
    ammoText = padSprite(ammoText, ammoTextPaddingConfig);


    let weaponFrame_startY = 2 + currWeapon * 12;

    let weaponToUse = currWeapon == 0 ? handgunSprite : currWeapon == 1 ? machinegunSprite : shotgunSprite;
    let weaponImage;
    if (weaponAnimTime == -1)
    {
        weaponImage = weaponToUse.getSprite('Idle');        
    }
    else
    {
        let t = weaponAnimTime / 100;
        t = 1 - t; // [0, 1): Animation; 1: Still
        weaponImage = weaponToUse.getAnimationSprite(t, 'Shoot');
    }

    //#endregion

    //weaponImage = padSprite(weaponImage, weaponImagePaddingConfig); Note that all padding for static sprites is now down once within spriteReader

    let objectArray = [];
    let objectStartIndezes = [];
    let objectBounds = [];
    let objectCount = 0;

    for (let i = 0; i < max_opponents * max_bullets * max_corpses; i++)
    {
        objectStartIndezes.push(0);
        objectBounds.push([0, 0, 0, 0]);
    }

    function addObjects(maxCount, rec_objects, presentObject_Function, defaultObject)
    {
        for (let i = 0; i < maxCount; i++)
        {
            let newObject;

            if (i < rec_objects.length)
            {
                let x = rec_objects[i][x_coordinate_key];
                let y = rec_objects[i][y_coordinate_key];

                newObject = presentObject_Function(rec_objects[i]);
                
                objectStartIndezes[objectCount] = objectArray.length;
                objectBounds[objectCount] = [x, y, newObject[0].length, newObject.length];
                objectCount++;
            }
            else
            {
                newObject = defaultObject;
            }

            objectArray = objectArray.concat(newObject.flat(1));
        }
    }

    addObjects(max_opponents, rec_opponents, (object) =>
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
        let delta = getDeltaBetweenAngles(object[direction_key], angleToOpponent);

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
            animationName = 'Idle';
        }
        else
        {
            animationName = 'Walk';

            let animTime = 20;
            t /= animTime;

            // Check whether opponent moves in opposite direction (angle between movement and looking >90)
            let movementDelta = getDeltaBetweenAngles(object[direction_key], object[direction_move_key]);
            if (movementDelta > PI*0.5 || movementDelta < -PI*0.5)
                t = 1 - t;
        }
        
        return playerSprite.getAnimationSprite(t, animationName + '_' + spriteDir);

    }, playerSprite.getSprite('Idle_N'));
    addObjects(max_bullets, rec_bullets, () => fireBulletSprite.getSprite('Idle_S'), fireBulletSprite.getSprite('Idle_S'));
    addObjects(max_corpses, rec_corpses, (object) =>
    {
        let corpse;
        let t = object[duration_key];
        let totalTime = 600;
        let animTime = 20;
        t -= totalTime - animTime;
        if (t > 0)
        {
            t = t / animTime;
            t = 1 - t;
            corpse = corpseSprite.getAnimationSprite(t, 'Explode');
        }
        else
        {
            corpse = corpseSprite.getSprite('Idle');
        }
        return corpse;
        
    }, corpseSprite.getSprite('Idle'));

    buffer = gpu_kernel(playerX, playerY, playerAngle,
        map_numbers,
        wallSprite.data, floorSprite.data, ceilingSprite.data, statusBarSprite.data, weaponFrameSprite.data,
        weaponImage, weaponImageBounds,
        healthText, ammoText,
        weaponFrame_startY,
        objectArray, objectStartIndezes, objectBounds, objectCount);
}

function drawingHandler_draw_gpu_single(playerX, playerY, playerAngle,      // Coordinates and Angle
    map_numbers,                                                            // Map
    wallSprite, floorSprite, ceilingSprite, statusBarSprite, weaponFrameSprite,    // World Sprites                                              
    weaponImage, weaponImageBounds,
    healthText, bulletsText,            // Status-Bar-Texts
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

    //#region Health-Text
    {
        let startX = this.constants.healthTextBounds_startX;
        let startY = this.constants.healthTextBounds_startY;
        let textSizeX = this.constants.healthTextBounds_sizeX;
        let textSizeY = this.constants.healthTextBounds_sizeY;
        let scale = this.constants.healthTextBounds_scale;
        let endX = startX + (textSizeX * scale);
        let endY = startY + (textSizeY * scale);

        if (x >= startX && x < endX && y >= startY && y < endY)
        {
            let pix_x = Math.floor((x - startX) / scale);
            let pix_y = Math.floor((y - startY) / scale);

            if (healthText[pix_y][pix_x][3] > 0)
            {
                r = healthText[pix_y][pix_x][0]
                g = healthText[pix_y][pix_x][1]
                b = healthText[pix_y][pix_x][2]

                depthBuffer = 0;
            }
        }        
    }
    //#endregion

    //#region Bullets-Text
    {
        let startX = this.constants.ammoTextBounds_startX;
        let startY = this.constants.ammoTextBounds_startY;
        let textSizeX = this.constants.ammoTextBounds_sizeX;
        let textSizeY = this.constants.ammoTextBounds_sizeY;
        let scale = this.constants.ammoTextBounds_scale;
        let endX = startX + (textSizeX * scale);
        let endY = startY + (textSizeY * scale);
    
        if (x >= startX && x < endX && y >= startY && y < endY)
        {
            let pix_x = Math.floor((x - startX) / scale);
            let pix_y = Math.floor((y - startY) / scale);
    
            if (bulletsText[pix_y][pix_x][3] > 0)
            {
                r = bulletsText[pix_y][pix_x][0]
                g = bulletsText[pix_y][pix_x][1]
                b = bulletsText[pix_y][pix_x][2]
    
                depthBuffer = 0;
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

    //#region Gun-Img
    if (depthBuffer > 0)
    {
        let spriteWidth = weaponImageBounds[0], spriteHeight = weaponImageBounds[1];
        let gun_spriteRatio = spriteWidth / spriteHeight;

        let gun_ImgHeight = this.constants.gun_Height;
        let gun_ImgWidth = gun_ImgHeight * gun_spriteRatio;
        let gun_yMin = gameWindowHeight - gun_ImgHeight;
        let gun_xMin = (screenWidth - gun_ImgWidth) * 0.5;
        let gun_xMax = screenWidth - gun_xMin;
        if (y >= gun_yMin && x >= gun_xMin && x <= gun_xMax)
        {
            let pix_x = Math.floor(((x - gun_xMin) / gun_ImgWidth) * spriteWidth);
            let pix_y = Math.floor(((y - gun_yMin) / gun_ImgHeight) * spriteHeight);
            
            if (weaponImage[pix_y][pix_x][3] > 0)
            {
                r = weaponImage[pix_y][pix_x][0]
                g = weaponImage[pix_y][pix_x][1]
                b = weaponImage[pix_y][pix_x][2]

                depthBuffer = 0;
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
                let objX = objectBounds[object][0];//corpses[corpses_startIndezes[corpse]][0];
                let objY = objectBounds[object][1];//corpses[corpses_startIndezes[corpse]][1];
                let spriteWidth = objectBounds[object][2];//corpses[corpses_startIndezes[corpse]][2];
                let spriteHeight = objectBounds[object][3];//corpses[corpses_startIndezes[corpse]][3];

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
                    let objCeiling = (screenHeight * 0.5) - (screenHeight / dstFromPlayer);
                    let objFloor = screenHeight - objCeiling;
                    let objHeight = objFloor - objCeiling;
                    let objRatio = spriteWidth / spriteHeight;
                    let objWidth = objHeight * objRatio;
                    let middleOfObject = (0.5 * (objAngle / (fov * 0.5)) + 0.5) * screenWidth;

                    // Absolutely zero idea what the following does and why the f*ck it works... It just works okay?! It just works... for now...
                    // Also, note that this only seems to work for fov = PI / 3, we probably need to adapt that sh*t calculation for other fovs.
                    if (middleOfObject < 0 + objWidth * 0.5) middleOfObject += screenWidth * 3;
                    if (middleOfObject > screenWidth * 3 - objWidth * 0.5) middleOfObject -= screenWidth * 3;

                    let objMinX = middleOfObject - objWidth * 0.5;
                    let objMaxX = middleOfObject + objWidth * 0.5;
                    let objMinY = screenHeight * 0.5 - objHeight * 0.5;
                    let objMaxY = screenHeight * 0.5 + objHeight * 0.5;

                    if (x >= objMinX && x <= objMaxX && y >= objMinY && y <= objMaxY)
                    {
                        let pix_x = Math.floor(((x - objMinX) / objWidth) * spriteWidth);
                        let pix_y = Math.floor(((objMaxY - y) / objHeight) * spriteHeight);

                        let offset = objectStartIndezes[object];
                        if (objectArray[offset + pix_y * spriteWidth + pix_x][3] > 0)  // If not transparent
                        {
                            r = objectArray[offset + pix_y * spriteWidth + pix_x][0]; //r = corpses[offset + pix_y][pix_x][0];
                            g = objectArray[offset + pix_y * spriteWidth + pix_x][1]; //g = corpses[offset + pix_y][pix_x][1];
                            b = objectArray[offset + pix_y * spriteWidth + pix_x][2]; //b = corpses[offset + pix_y][pix_x][2];
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