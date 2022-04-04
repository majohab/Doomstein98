// Config
const cellSize = 4; // Pixels per side of cell
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
            statusBar_Height: screenHeight / 8,
            gun_Height: screenHeight / 5,

            fov: fov,
            depth: depth_gpu,
            depth_step_gpu: depth_step_gpu,

            mapWidth: mapWidth,
            mapHeight: mapHeight,

            wallHeight: wallHeight,

            wallSprite_width: 6,
            wallSprite_height: 6,
            wallSprite_iterations_x: 2,
            wallSprite_iterations_y: 2,
            floorSprite_width: 6,
            floorSprite_height: 6,
            floorSprite_iterations_x: 2,
            floorSprite_iterations_y: 2,
            ceilingSprite_width: 2,
            ceilingSprite_height: 2,
            ceilingSprite_iterations_x: 1,
            ceilingSprite_iterations_y: 1,

            statusBarSprite_width: 644,
            statusBarSprite_height: 77,

            gunSprite_width: 128,
            gunSprite_height: 88
        }
    };
    gpu_kernel = gpu.createKernel(
        function(playerX, playerY, playerAngle, map_numbers, wallSprite, floorSprite, ceilingSprite, statusBarSprite, gunSprite, bulletSprite) {
            drawingHandler_draw_gpu_single(playerX, playerY, playerAngle, map_numbers, wallSprite, floorSprite, ceilingSprite, statusBarSprite, gunSprite, bulletSprite);
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
    buffer = gpu_kernel(playerX, playerY, playerAngle, map_numbers, wallSprite.data, floorSprite.data, ceilingSprite.data, statusBarSprite.data, gunSprite.data, bulletSprite.data);
}

function drawingHandler_draw_gpu_single(playerX, playerY, playerAngle, map_numbers, wallSprite, floorSprite, ceilingSprite, statusBarSprite, gunSprite, bulletSprite)
{
    let screenWidth = this.constants.screenWidth;
    let screenHeight = this.constants.screenHeight;
    let statusBarHeight = this.constants.statusBar_Height;

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

    if (y <= gameWindowHeight) // Main-Screen
    {
        //#region Init

        let r = 0;
        let g = 0;
        let b = 0;
        let a = 0;

        //#endregion

        //#region Gun-Img
        
        let gun_spriteRatio = this.constants.gunSprite_width / this.constants.gunSprite_height;

        let gun_ImgHeight = this.constants.gun_Height;
        let gun_ImgWidth = gun_ImgHeight * gun_spriteRatio;
        let gun_yMin = gameWindowHeight - gun_ImgHeight;
        let gun_xMin = (screenWidth - gun_ImgWidth) * 0.5;
        let gun_xMax = screenWidth - gun_xMin;
        if (y >= gun_yMin && x >= gun_xMin && x <= gun_xMax)
        {
            let pix_x = Math.floor(((x - gun_xMin) / gun_ImgWidth) * this.constants.gunSprite_width);
            let pix_y = Math.floor(((gameWindowHeight - y) / gun_ImgHeight) * this.constants.gunSprite_height);
            
            r = gunSprite[pix_y][pix_x][0]
            g = gunSprite[pix_y][pix_x][1]
            b = gunSprite[pix_y][pix_x][2]
            a = gunSprite[pix_y][pix_x][3]
        }
        
        //#endregion

        //#region 3D Ray-Casting

        if (a == 0)
        {

            let fov = this.constants.fov;
            let depth = this.constants.depth;
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
            a = 255;
        }

        //#endregion
        
        this.color(r / 255, g / 255, b / 255, a / 255)
    }
    else // Status-Bar
    {
        let localY = y - gameWindowHeight;

        let spriteWidth = this.constants.statusBarSprite_width;
        let spriteHeight = this.constants.statusBarSprite_height;

        let pix_x = Math.floor((x / screenWidth) * spriteWidth);
        let pix_y = Math.floor((localY / statusBarHeight) * spriteHeight);
        pix_y = spriteHeight - pix_y - 1;

        this.color(
            statusBarSprite[pix_y][pix_x][0] / 255,
            statusBarSprite[pix_y][pix_x][1] / 255,
            statusBarSprite[pix_y][pix_x][2] / 255,
            1
        )
    }
}

//#endregion