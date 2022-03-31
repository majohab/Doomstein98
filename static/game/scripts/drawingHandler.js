// Config
const useGPU = true;
const cellSize = 4;
const wallHeight = 1.5;
const depth_cpu = 16.0;
const depth_gpu = 32.0;
const depth_step_cpu = 0.1;
const depth_step_gpu = 0.05;

// Runtime variables
let canvas;
let ctx;
let screenWidth;
let screenHeight;

let buffer;

let gpu;
let gpu_kernel;
let gpu_kernel_settings;


function drawingHandler_init()
{
    if (useGPU)
    {
        screenWidth = 1000;
        screenHeight = 800;

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
                fov: fov,
                depth: depth_gpu,
                mapWidth: mapWidth,
                mapHeight: mapHeight,
                wallHeight: wallHeight,
                cellSize: cellSize,
                depth_step_gpu: depth_step_gpu
            }
        };
        gpu_kernel = gpu.createKernel(
            function(playerX, playerY, playerAngle, map_numbers, wallSprite, floorSprite, skySprite) {
                drawingHandler_draw_gpu_single(playerX, playerY, playerAngle, map_numbers, wallSprite, floorSprite, skySprite);
            },
            gpu_kernel_settings
        );
        
        canvas = gpu_kernel.canvas;
    }
    else
    {
        screenWidth = 250;
        screenHeight = 200;

        canvas = document.createElement('canvas');
        canvas.setAttribute('width', 1000);
        canvas.setAttribute('height', 800);

        buffer = [];
        for (x = 0; x < screenWidth; x++)
        {
            buffer.push([]);
            for (y = 0; y < screenHeight; y++)
            {
                buffer[x].push("");
            }
        }
    
        //         <canvas id="canvas" width="1000" height="750"></canvas>
    }

    document.getElementById("canvas-container").appendChild(canvas);
    
    ctx = canvas.getContext("2d");
}

function drawingHandler_drawCells()
{
    if (useGPU)
        drawingHandler_draw_gpu();
    else
    {
        drawingHandler_cpu_clearScreen();
        drawingHandler_draw_cpu_calculateBuffer();
        drawingHandler_draw_cpu_drawFromBuffer();
    }
}

//#region CPU

function drawingHandler_cpu_clearScreen()
{
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function drawingHandler_draw_cpu_calculateBuffer()
{
    for (x = 0; x < screenWidth; x++)
    {
        let rayAngle = (playerAngle - fov * 0.5) + (x / screenWidth) * fov;
    
        let distanceToWall = 0;
        let hitWall = false;
    
        // eye: Unit-vector for ray in player-space
        let eyeX = Math.sin(rayAngle);
        let eyeY = Math.cos(rayAngle);
    
        let sampleX_wall = 0;
    
        while (!hitWall && distanceToWall < depth_cpu)
        {      
            distanceToWall += depth_step_cpu;
            
            let testX = Math.floor(playerX + eyeX * distanceToWall);
            let testY = Math.floor(playerY + eyeY * distanceToWall);
            
            if (testX < 0 || testX >= mapWidth || testY < 0 || testY >= mapHeight) // Out of map bounds
            {
                hitWall = true;
                distanceToWall = depth_cpu;
            }
            else if (map[testY].charAt(testX) == '#')
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
        
    
        for (y = 0; y < screenHeight; y++)
        {
            let sampleX;
            let sampleY;
            let sprite;
           
            if (y >= ceiling && y <= floor) // Wall
            {
                sampleX = sampleX_wall;
                let sampleY_percent = (y - ceiling) / (floor - ceiling); // percent-value between floor and ceiling
                sampleY = sampleY_percent * wallHeight;
                //console.log(wallSprite.getImageData(sampleX, sampleY, 1, 1).data);
            
                sprite = wallSprite;
                //ctx.fillStyle = "rgb(" + sampleX * 255 + "," + sampleX * 255 + "," + sampleX * 255 + ")"; // fill(100 / (distanceToWall / depth_cpu));
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
    
                    sprite = skySprite;
    
                    //ctx.fillStyle = "rgb(0,0,0)";
                }
                else // Floor
                {
                    // 1: 0.66, 1.5: 0.45, 2: 0.33
                    sampleX = rowDistance * eyeX + playerX * (0.66 / wallHeight); // Zero idea why (0.66 / wallHeight)... It was a late sunday evening and this number just did the trick ^^'
                    sampleX -= Math.floor(sampleX);
                    sampleY = rowDistance * eyeY + playerY * (0.66 / wallHeight);
                    sampleY -= Math.floor(sampleY);

                    sprite = floorSprite;
                }

                //ctx.fillStyle = "rgb(" + sampleY * 255 + "," + sampleY * 255  + "," + sampleY * 255   + ")";
            }

            let imageData = sprite.getPixel(sampleX, sampleY);

            buffer[x][y] = imageData;
        }
    }
}

function drawingHandler_draw_cpu_drawFromBuffer()
{
    for (x = 0; x < screenWidth; x++)
    {
        for (y = 0; y < screenHeight; y++)
        {
            ctx.fillStyle = "rgb(" + buffer[x][y][0] + "," + buffer[x][y][1] + "," + buffer[x][y][2] + ")";;
            ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        }
    }
}

//#endregion

//#region  GPU

function drawingHandler_draw_gpu()
{
    buffer = gpu_kernel(playerX, playerY, playerAngle, map_numbers, wallSprite.data, floorSprite.data, skySprite.data);
}

function drawingHandler_draw_gpu_single(playerX, playerY, playerAngle, map_numbers, wallSprite, floorSprite, skySprite)
{
    let screenWidth = this.constants.screenWidth;
    let screenHeight = this.constants.screenHeight;
    let fov = this.constants.fov;
    let depth = this.constants.depth;
    let mapWidth = this.constants.mapWidth;
    let mapHeight = this.constants.mapHeight;
    let wallHeight = this.constants.wallHeight;

    // Read values (y must be inverted, we're looking from bottom this time)
    let x = this.thread.x;
    let y = screenHeight-this.thread.y;
    // Round all pixels within cell to left of the cell
    x = Math.floor(x / this.constants.cellSize) * this.constants.cellSize;
    y = Math.round(y / this.constants.cellSize) * this.constants.cellSize;
    // Center of the cell
    x += this.constants.cellSize * 0.5
    y += this.constants.cellSize * 0.5;

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
        
            //sprite = skySprite;
        
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

    let spriteWidth = spriteIndex == 0 || spriteIndex == 1 ? 6 : 2;
    let spriteHeight = spriteWidth;
    let iterations_x = spriteIndex == 0 || spriteIndex == 1 ? 2 : 1;
    let iterations_y = iterations_x;

    let uv_x = Math.floor(sampleX * spriteWidth * iterations_x) % spriteWidth;
    let uv_y = Math.floor(sampleY * spriteHeight * iterations_y) % spriteHeight;

    this.color(
        (spriteIndex == 0 ? wallSprite[uv_y][uv_x][0] : spriteIndex == 1 ? floorSprite[uv_y][uv_x][0] : skySprite[uv_y][uv_x][0]) / 255,
        (spriteIndex == 0 ? wallSprite[uv_y][uv_x][1] : spriteIndex == 1 ? floorSprite[uv_y][uv_x][1] : skySprite[uv_y][uv_x][1]) / 255,
        (spriteIndex == 0 ? wallSprite[uv_y][uv_x][2] : spriteIndex == 1 ? floorSprite[uv_y][uv_x][2] : skySprite[uv_y][uv_x][2]) / 255,
        1);
    //return [wallSprite[uv_y][uv_x][0], wallSprite[uv_y][uv_x][1], wallSprite[uv_y][uv_x][2]];

}

//#endregion