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
    for (x = 0; x < screenWidth; x++)
    {
        let rayAngle = (playerAngle - fov * 0.5) + (x / screenWidth) * fov;
    
        let distanceToWall = 0;
        let hitWall = false;
    
        // eye: Unit-vector for ray in player-space
        let eyeX = Math.sin(rayAngle);
        let eyeY = Math.cos(rayAngle);
    
        let sampleX = 0;
    
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
                    sampleX = testPointY - testY;
                if (testAngle >= Math.PI * 0.25 && testAngle < Math.PI * 0.75)
                    sampleX = testPointX - testX;
                if (testAngle < -Math.PI * 0.25 && testAngle >= -Math.PI * 0.75)
                    sampleX = testPointX - testX;
                if (testAngle >= Math.PI * 0.75 || testAngle < -Math.PI * 0.75)
                    sampleX = testPointY - testY;
            }
        }
    
        let ceiling = ((screenHeight * 0.5) - ((screenHeight / distanceToWall)) * (screenHeight / screenWidth) * wallHeight);
        let floor = screenHeight - ceiling;
        
    
        for (y = 0; y < screenHeight; y++)
        {
            if (y < ceiling) // Ceiling
                ctx.fillStyle = "rgb(0,0,0)";
            else if (y > ceiling && y <= floor) // Wall
            {
                let sampleY_percent = (y - ceiling) / (floor - ceiling); // percent-value between floor and ceiling
                let sampleY = sampleY_percent * wallHeight;
                //console.log(wallSprite.getImageData(sampleX, sampleY, 1, 1).data);
            
                let imageData = wallSprite.getPixel(sampleX, sampleY);
                //ctx.fillStyle = "rgb(" + sampleX * 255 + "," + sampleX * 255 + "," + sampleX * 255 + ")"; // fill(100 / (distanceToWall / depth));
                ctx.fillStyle = "rgb(" + imageData[0] + "," + imageData[1] + "," + imageData[2] + ")";
            }
            else // Floor
            {
                let dirX = Math.sin(playerAngle),
                    dirY = Math.cos(playerAngle);        //initial direction vector
                let planeX = dirY,
                    planeY = -dirX * 0.6;    //the 2d raycaster version of camera plane
            
                // rayDir for leftmost ray (x = 0) and rightmost ray (x = w)
                let rayDirX0 = dirX - planeX;
                let rayDirY0 = dirY - planeY;
                let rayDirX1 = dirX + planeX;
                let rayDirY1 = dirY + planeY;
            
                // Current y position compared to the center of the screen (the horizon)
                let p = y - screenHeight * 0.5;
            
                // Vertical position of the camera.
                let posZ = 0.5 * screenHeight;
            
                // Horizontal distance from the camera to the floor for the current row.
                // 0.5 is the z position exactly in the middle between floor and ceiling.
                let rowDistance = posZ / p;
            
                // calculate the real world step vector we have to add for each x (parallel to camera plane)
                // adding step by step avoids multiplications with a weight in the inner loop
                //let floorStepX = rowDistance * (rayDirX1 - rayDirX0) / screenWidth;
                //let floorStepY = rowDistance * (rayDirY1 - rayDirY0) / screenWidth;
            
                //// real world coordinates of the leftmost column. This will be updated as we step to the right.
                //let floorX = playerX + rowDistance * rayDirX0;
                //let floorY = playerY + rowDistance * rayDirY0;

                //let sampleX = floorX + x * floorStepX;
                //sampleX -= Math.floor(sampleX);
                //let sampleY = floorY + x * floorStepY;
                //sampleY -= Math.floor(sampleY);

                let sampleX = rowDistance * eyeX + playerX * 0.45;
                sampleX -= Math.floor(sampleX);
                let sampleY = rowDistance * eyeY + playerY * 0.45;
                sampleY -= Math.floor(sampleY);

                let imageData = floorSprite.getPixel(sampleX, sampleY);

                //ctx.fillStyle = "rgb(" + sampleY * 255 + "," + sampleY * 255  + "," + sampleY * 255   + ")";
                



                //currentDist = screenHeight / (2.0 * y - screenHeight); // distance from real-world pixel to player
//
                //let weight = currentDist / distanceToWall;
//
                //let currentFloorX = weight * 1 + (1.0 - weight) * playerX;
                //let currentFloorY = weight * 1 + (1.0 - weight) * playerY;

                //let imageData = floorSprite.getPixel(currentFloorX, currentFloorY);

                //ctx.fillStyle = "rgb(30,30,30)";

                       
                //let sampleY = (y - floor) / (floor - ceiling);
                //sampleY = sampleY * (screenHeight - floor);
                //sampleY = sampleY / (screenHeight * 0.5);

                ctx.fillStyle = "rgb(" + imageData[0] + "," + imageData[1] + "," + imageData[2] + ")";
            }
        
            ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        }
    }
}