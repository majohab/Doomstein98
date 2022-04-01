// Config
const cellSize = 4; // Pixels per side of cell
const wallHeight = 1.5;
const depth_cpu = 16.0;
const depth_gpu = 32.0;
const depth_step_cpu = 0.1;
const depth_step_gpu = 0.05;
const statusBar_Height = 150; // Measured in pixels

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

    gpu = new GPU();
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
            statusBar_Height: statusBar_Height,

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

            statusBarSprite_width: 160,
            statusBarSprite_height: 19
        }
    };
    gpu_kernel = gpu.createKernel(
        function(playerX, playerY, playerAngle, map_numbers, wallSprite, floorSprite, ceilingSprite, statusBarSprite) {
            drawingHandler_draw_gpu_single(playerX, playerY, playerAngle, map_numbers, wallSprite, floorSprite, ceilingSprite, statusBarSprite);
        },
        gpu_kernel_settings
    );
    
    canvas = gpu_kernel.canvas;

    document.getElementById("canvas-container").appendChild(canvas);
    
    ctx = canvas.getContext("2d");
}

function drawingHandler_drawCells()
{
    drawingHandler_draw_gpu();
}

//#region  GPU

function drawingHandler_draw_gpu()
{
    buffer = gpu_kernel(playerX, playerY, playerAngle, map_numbers, wallSprite.data, floorSprite.data, ceilingSprite.data, statusBarSprite.data);
}

function drawingHandler_draw_gpu_single(playerX, playerY, playerAngle, map_numbers, wallSprite, floorSprite, ceilingSprite, statusBarSprite)
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
                // 1: 0.66, 1.5: 0.45, 2: 0.33
                 // Zero idea why (0.65 / wallHeight)... It was a late sunday evening and this number just did the trick ^^'
                let constant = 0.63; // Lower: floor moves in direction of player. Higher: floor moves in opposite direction
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

        let uv_x = Math.floor(sampleX * spriteWidth * iterations_x) % spriteWidth;
        let uv_y = Math.floor(sampleY * spriteHeight * iterations_y) % spriteHeight;
        
        uv_y = spriteHeight - uv_y - 1;

        this.color(
            (spriteIndex == 0 ? wallSprite[uv_y][uv_x][0] : spriteIndex == 1 ? floorSprite[uv_y][uv_x][0] : ceilingSprite[uv_y][uv_x][0]) / 255,
            (spriteIndex == 0 ? wallSprite[uv_y][uv_x][1] : spriteIndex == 1 ? floorSprite[uv_y][uv_x][1] : ceilingSprite[uv_y][uv_x][1]) / 255,
            (spriteIndex == 0 ? wallSprite[uv_y][uv_x][2] : spriteIndex == 1 ? floorSprite[uv_y][uv_x][2] : ceilingSprite[uv_y][uv_x][2]) / 255,
            1);
        //return [wallSprite[uv_y][uv_x][0], wallSprite[uv_y][uv_x][1], wallSprite[uv_y][uv_x][2]];
    }
    else // Status-Bar
    {
        let localY = y - gameWindowHeight;

        let spriteWidth = this.constants.statusBarSprite_width;
        let spriteHeight = this.constants.statusBarSprite_height;

        let uv_x = Math.floor((x / screenWidth) * spriteWidth);
        let uv_y = Math.floor((localY / statusBarHeight) * spriteHeight);
        uv_y = spriteHeight - uv_y - 1;

        this.color(
            statusBarSprite[uv_y][uv_x][0] / 255,
            statusBarSprite[uv_y][uv_x][1] / 255,
            statusBarSprite[uv_y][uv_x][2] / 255
        )
    }
}

//#endregion