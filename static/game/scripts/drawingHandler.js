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


function drawingHandler_init()
{
    screenWidth = 1200;
    screenHeight = 900;

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

            bulletSprite_width: bulletSprite.width,
            bulletSprite_height: bulletSprite.height,

            weaponFrameSprite_width: weaponFrameSprite.width,
            weaponFrameSprite_height: weaponFrameSprite.height
        }
    };
    gpu_kernel = gpu.createKernel(
        function(playerX, playerY, playerAngle, 
            map_numbers,
            wallSprite, floorSprite, ceilingSprite, statusBarSprite, bulletSprite, weaponFrameSprite,
            bullets, bullets_length,
            weaponImage, weaponImageBounds,
            healthText, healthTextBounds, bulletsText, bulletsTextBounds,
            weaponFrame_startY) {
            drawingHandler_draw_gpu_single(playerX, playerY, playerAngle, 
                map_numbers,
                wallSprite, floorSprite, ceilingSprite, statusBarSprite, bulletSprite, weaponFrameSprite,
                bullets, bullets_length,
                weaponImage, weaponImageBounds,
                healthText, healthTextBounds, bulletsText, bulletsTextBounds,
                weaponFrame_startY);
        },
        gpu_kernel_settings
    );
    
    
}

function drawingHandler_drawCells()
{
    drawingHandler_draw_gpu();
}

//#region  GPU

function drawingHandler_draw_gpu()
{
    let healthText = getHealthText();
    healthText = padSprite(healthText, healthTextBounds[2], healthTextBounds[3], -1, 0);

    let ammoText = getAmmoText();
    ammoText = padSprite(ammoText, ammoTextBounds[2], ammoTextBounds[3], -1, 0);

    let weaponFrame_startY = 2 + currWeapon * 12;
    
    let weaponImage = currWeapon == 0 ? handgun.getSprite(0) : currWeapon == 1 ? machinegun.getSprite(0) : shotgun.getSprite(0);
    weaponImage = padSprite(weaponImage, weaponImageBounds[0], weaponImageBounds[1], 0, 1);
    //console.log(weaponImage);

    buffer = gpu_kernel(playerX, playerY, playerAngle,
        map_numbers,
        wallSprite.data, floorSprite.data, ceilingSprite.data, statusBarSprite.data, bulletSprite.data, weaponFrameSprite.data,
        bullets, bulletCount,
        weaponImage, weaponImageBounds,
        healthText, healthTextBounds, ammoText, ammoTextBounds,
        weaponFrame_startY);
}

function drawingHandler_draw_gpu_single(playerX, playerY, playerAngle,      // Coordinates and Angle
    map_numbers,                                                            // Map
    wallSprite, floorSprite, ceilingSprite, statusBarSprite, bulletSprite, weaponFrameSprite,    // World Sprites
    bullets, bullets_length,                                                // Bullets
    weaponImage, weaponImageBounds,
    healthText, healthTextBounds, bulletsText, bulletsTextBounds,           // Status-Bar-Texts
    weaponFrame_startY)                                                     // Status-Bar-Weapon-Frame
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
        let startX = healthTextBounds[0];
        let startY = healthTextBounds[1];
        let textSizeX = healthTextBounds[2];
        let textSizeY = healthTextBounds[3];
        let scale = healthTextBounds[4];
        let endX = startX + (textSizeX * scale);
        let endY = startY + (textSizeY * scale);

        if (x >= startX && x < endX && y >= startY && y < endY)
        {
            let pix_x = Math.floor((x - startX) / scale);
            let pix_y = Math.floor((y - startY) / scale);

            if (healthText[4 * (pix_y * 46 + pix_x) + 3] > 0)
            {
                r = healthText[4 * (pix_y * 46 + pix_x) + 0]
                g = healthText[4 * (pix_y * 46 + pix_x) + 1]
                b = healthText[4 * (pix_y * 46 + pix_x) + 2]

                depthBuffer = 0;
            }
        }        
    }
    //#endregion

    //#region Bullets-Text
    {
        let startX = bulletsTextBounds[0];
        let startY = bulletsTextBounds[1];
        let textSizeX = bulletsTextBounds[2];
        let textSizeY = bulletsTextBounds[3];
        let scale = bulletsTextBounds[4];
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

            if (y < ceiling) // Ceiling
            {
            
                sampleX = rowDistance * eyeX; // Zero idea why (0.66 / wallHeight)... It was a late sunday evening and this number just did the trick ^^'
                sampleX -= Math.floor(sampleX);
                sampleY = rowDistance * eyeY;
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

        //#region Bullets

        for (let obj = 0; obj < bullets_length; obj++) // First element is 0
        {
            let objX = bullets[obj][0];
            let objY = bullets[obj][1];
            let spriteWidth = this.constants.bulletSprite_width;
            let spriteHeight = this.constants.bulletSprite_height;

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

                    if (bulletSprite[pix_y][pix_x][3] > 0)  // If not transparent
                    {
                        r = bulletSprite[pix_y][pix_x][0];
                        g = bulletSprite[pix_y][pix_x][1];
                        b = bulletSprite[pix_y][pix_x][2];

                        depthBuffer = dstFromPlayer;
                    }
                }
            }
        }

        //#endregion
    }

    //#endregion
            
    this.color(r / 255, g / 255, b / 255)
}

//#endregion