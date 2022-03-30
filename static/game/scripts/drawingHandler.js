// Config
const cellSize = 4;
const wallHeight = 1.5;
const depth = 16.0;

// Runtime variables
let ctx;
let screenWidth;
let screenHeight;

function drawingHandler_init()
{
    ctx = canvas.getContext("2d");

    screenWidth = canvas.width / cellSize;
    screenHeight = canvas.height / cellSize;
}

function drawingHandler_clearScreen()
{
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function drawingHandler_drawCells()
{
    drawingHandler_drawCells_cpu();
}

function drawingHandler_drawCells_cpu()
{
    let buffer = [];

    for (x = 0; x < screenWidth; x++)
    {
        buffer.push([]);

        let rayAngle = (playerAngle - fov * 0.5) + (x / screenWidth) * fov;
    
        let distanceToWall = 0;
        let hitWall = false;
    
        // eye: Unit-vector for ray in player-space
        let eyeX = Math.sin(rayAngle);
        let eyeY = Math.cos(rayAngle);
    
        let sampleX_wall = 0;
    
        while (!hitWall && distanceToWall < depth)
        {      
            distanceToWall += 0.1;
            
            let testX = Math.floor(playerX + eyeX * distanceToWall);
            let testY = Math.floor(playerY + eyeY * distanceToWall);
            
            if (testX < 0 || testX >= mapWidth || testY < 0 || testY >= mapHeight) // Out of map bounds
            {
                hitWall = true;
                distanceToWall = depth;
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
                sampleY_percent = (y - ceiling) / (floor - ceiling); // percent-value between floor and ceiling
                sampleY = sampleY_percent * wallHeight;
                //console.log(wallSprite.getImageData(sampleX, sampleY, 1, 1).data);
            
                sprite = wallSprite;
                //ctx.fillStyle = "rgb(" + sampleX * 255 + "," + sampleX * 255 + "," + sampleX * 255 + ")"; // fill(100 / (distanceToWall / depth));
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

            buffer.push("rgb(" + imageData[0] + "," + imageData[1] + "," + imageData[2] + ")");
        }
    }


    for (x = 0; x < screenWidth; x++)
    {
        for (y = 0; y < screenHeight; y++)
        {
            ctx.fillStyle = buffer[x][y];
        
            ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        }
    }
}
