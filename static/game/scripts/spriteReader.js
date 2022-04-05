class Sprite
{
    // https://gibberlings3.github.io/iesdp/file_formats/ie_formats/bmp.htm

    constructor(img, iterations_x, iterations_y) {
        
        // ToDo: Load from server

        function readBytes(string, i_start, length = 1)
        {
            let s = "0x";
            for (let i = i_start + length - 1; i >=  i_start; i--)
                s += string.charAt(i * 2) + string.charAt(i * 2 + 1);
            return parseInt(s);
        }

        //let info = img.substring(0, 54 * 2);  // bytes 0 -> 53 store information about the image; 54-byte header; unsigned char 0 -> 255 => size of a byte
        let width = readBytes(img, 18, 4);
        let height = readBytes(img, 22, 4);
        let bitOffset = readBytes(img, 10, 4);
        let bitCount = readBytes(img, 28, 2);

        // Pixel lines are padded with zeros to end on a 32bit (4byte) boundary. See: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/bmp.htm
        //  w | zuViel  | padding
        //  4 |     0   | 0
        //  5 |     1   | 3
        //  6 |     2   | 2
        //  7 |     3   | 1
        let paddingSize = bitCount == 32 ? 0 : (4 - (((width * 3) % 4))) % 4; // width * 3: 3 bytes per pixel. ((width * 3) % 4): count of bytes we're over 4*k. 4 - (...): [1, 4]. (...) % 4: [1, 4] -> [0, 3]

        // Store pixel colors
        
        let rawData = img.substring(bitOffset * 2, img.length);
        let data = []; // y, x, RGB
        let bytesPerPixel = bitCount == 24 ? 3 : 4;
        
        // In Bitmap, pixels are stored bottom-up, starting in the lower left corner, going from left to right and then row by row from the bottom to the top.
        for (let y = 0; y < height; y++) // Loop for every pixel, where every pixel has three bytes for Red, Green & Blue
        {                   
            data.push([]);         
            for (let x = 0; x < width; x++)
            {
                data[y].push([]);

                let i = (y * width + x) * bytesPerPixel + y * paddingSize; // Somehow at the end of the line there are two empty bits
                // By default, the first byte is Blue, the second Green, and the third Red; We'll flip them in the usual RGB order

                data[y][x].push(readBytes(rawData, i + 2));  // Red
                data[y][x].push(readBytes(rawData, i + 1));  // Green
                data[y][x].push(readBytes(rawData, i));      // Blue
                if (bytesPerPixel == 4) data[y][x].push(readBytes(rawData, i + 3)); // Alpha

                //console.log("Read new color: " + data[x][y][0] + ", " + data[x][y][1] + ", " + data[x][y][2]);
            }
        }

        this.data = data;
        this.width = width;
        this.height = height;
        this.iterations_x = iterations_x;
        this.iterations_y = iterations_y;

        //console.log("bfType: " + readBytes(img, 0, 2));
        //console.log("bfSize: " + readBytes(img, 2, 4));
        //console.log("bfReserved: " + readBytes(img, 6, 4));
        //console.log("bfOffBits: " + readBytes(img, 10, 4));
        //console.log("biSize: " + readBytes(img, 14, 4));
        //console.log("biWidth: " + readBytes(img, 18, 4));
        //console.log("biHeight: " + readBytes(img, 22, 4));
        //console.log("biPlanes: " + readBytes(img, 26, 2));
        //console.log("biBitCount: " + readBytes(img, 28, 2));
        //console.log("biCompression: " + readBytes(img, 30, 4));
        //console.log("biSizeImage: " + readBytes(img, 34, 4));
        //console.log("biXPelsPerMeter: " + readBytes(img, 38, 4));
        //console.log("biYPelsPerMeter: " + readBytes(img, 42, 4));
        //console.log("biClrUsed: " + readBytes(img, 46, 4));
        //console.log("biClrImportant: " + readBytes(img, 50, 4));
        //console.log(data);
    }

    getPixel(x_percent, y_percentRelativeToWidth) // x: [0, 1], y: [0, wallHeight]
        // Note that this method sadly cannot be used anymore with the new GPU-based system
    {
        let pix_x = Math.floor(x_percent * this.width * this.iterations_x) % this.width;
        let pix_y = Math.floor(y_percentRelativeToWidth * this.height * this.iterations_y) % this.height
        return this.data[pix_y][pix_x];
    }
}

let wallSprite;
let floorSprite;
let ceilingSprite;

let statusBarSprite;

let gunSprite;
let bulletSprite;

async function spriteReader_init()
{
    let inits = 0;
    const initCount = 6;

    spriteReader_getSpriteString('Wall',    (img) => { wallSprite = new Sprite(img, 2, 2); inits++; });
    spriteReader_getSpriteString('Floor',   (img) => { floorSprite = new Sprite(img, 1, 1); inits++; })
    spriteReader_getSpriteString('Sky',     (img) => { ceilingSprite = new Sprite(img, 1, 1); inits++; })

    spriteReader_getSpriteString('StatusBar_Doom',  (img) => { statusBarSprite = new Sprite(img, 1, 1); inits++; });

    spriteReader_getSpriteString('Shotgun_1_32Bit', (img) => { gunSprite = new Sprite(img, 1, 1); inits++; });
    spriteReader_getSpriteString('Bullet_1',        (img) => { bulletSprite = new Sprite(img, 1, 1); inits++; });

    // Check each checkIntervall ms whether all ressources are loaded now
    const checkIntervall = 50;
    while(inits != initCount)
        await new Promise(resolve => setTimeout(resolve, checkIntervall));

        console.log(bulletSprite.data);
}

function spriteReader_getSpriteString(spriteName, callback)
{
    $.ajax({
        type: 'GET',
        url: "/game/getSprite/" + spriteName,
        success: function (response) {
            callback(response['sprite_string']);
        },
        error: function (response) {
            console.log(response)
        }
    })
}