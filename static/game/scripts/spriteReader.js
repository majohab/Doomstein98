class Sprite
{
    // https://de.wikipedia.org/wiki/Windows_Bitmap
    // https://gibberlings3.github.io/iesdp/file_formats/ie_formats/bmp.htm

    constructor(img, iterations_x, iterations_y)
    {
        
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

class Still
{
    constructor(identifier, startX, startY, sizeX, sizeY, padding)
    {
        this.identifier = identifier;
        this.startX = startX;
        this.startY = startY;
        this.sizeX = sizeX;
        this.sizeY = sizeY;
        this.padding = padding;
    }
}

class StillSequence
{
    constructor(identifier, sprites)
    {
        this.identifier = identifier;
        this.sprites = sprites;
    }
}

class SpriteSet
{
    constructor(img, stills, animations, flipped = false)
    {
        let imgData = new Sprite(img, 1, 1).data;

        let imgHeight = imgData.length;

        //console.log ('Loaded imgData for Font:');
        //console.log (imgData); 

        let dict = {};

        function getStillData(still)
        {
            let stillData = [];

            for (let y = 0; y < still.sizeY; y++)
            {
                stillData.push([]);
                for (let x = 0; x < still.sizeX; x++)
                {
                    stillData[y].push([]);
                }
            }

            for (let y = 0; y < still.sizeY; y++)
            {
                for (let x = 0; x < still.sizeX; x++)
                {
                    let img_y = imgHeight - (still.startY + y) - 1;
                    let still_y = flipped ? y : (still.sizeY - y - 1);
                    stillData[still_y][x] = imgData[img_y][still.startX + x];
                }
            }

            if (still.padding != null && typeof still.padding != undefined)
                stillData = padSprite (stillData, still.padding);
            
            return stillData;
        }

        for (let still of stills)
        {
            dict[still.identifier] = getStillData(still);

            //console.log('New Letter: ');
            //console.log(letterData);
        }

        if (animations != null && typeof animations != undefined)
        {
            for (let animation of animations)
            {
                dict[animation.identifier] = [];
                for (let still of animation.sprites)
                {
                    dict[animation.identifier].push(getStillData(still));
                }
            }
        }
        

        this.dict = dict;
        
        //console.log ('New SpriteSet: ' + JSON.stringify(dict));
    }

    getSprite(identifier)
    {
        return this.dict[identifier];
    }

    getAnimationSprite(t, animationIdentifier = 'Idle') // t: [0, 1]
    {
        if (!Array.isArray(this.dict[animationIdentifier][0][0][0])) // Still
        {
            return this.getSprite(animationIdentifier);
        }
        else    // Animation
        {
            // Example: 5 Sprites, Index 1 to 4 for Animation
            // [0, 0.25):   Index 1
            // [0.25, 0.5): Index 2
            // [0.5, 0.75): Index 3
            // [0.75, 1):   Index 4
            // 1:           Index 0
            let index = Math.floor(t * this.dict[animationIdentifier].length);
            return this.dict[animationIdentifier][index];
        }

        
    }
}

class Font extends SpriteSet
{
    getTextImg(text)
    {
        let dict = this.dict;
        let data = [];
        let textWidth = 0;
        let textHeight = 0;

        //console.log ("Generating image from text");

        for (let i = 0; i < text.length; i++)
        {
            let char = text.charAt(i);

            textWidth += dict[char][0].length;
            textHeight = Math.max(textHeight, dict[char].length);
        }
                
        //console.log ("with width = " + textWidth);
        //console.log ("and height = " + textHeight);

        for (let y = 0; y < textHeight; y++)
        {
            data.push([]);
            for (let x = 0; x < textWidth; x++)
            {
                data[y].push([]);

                let i = 0
                let currWidth = 0;
                let char;

                while (currWidth <= x)
                {
                    char = text.charAt(i);
                    currWidth += dict[char][0].length;

                    i++;
                }

                let letterData = dict[char];
                let letterWidth = letterData[0].length;
                let letterHeight = letterData.length
                let yMargin = (textHeight - letterHeight) * 0.5;

                if (y < yMargin || y >= textHeight - yMargin)
                    data[y][x].push([0, 0, 0, 0]); // ToDo: Don't just assume imgData is 32Bits
                else
                {
                    data[y][x] = letterData[y - yMargin][x - currWidth + letterWidth];
                }
            }
        }

        return data;
    }
}

class PaddingConfig
{
    constructor(destWidth, destHeight, // -1: Don't pad, use current value instead
    pad_x, // -1: left, 0: mid, 1: right
    pad_y) // -1: bottom, 0: mid, 1: top
    {
        this.destWidth = destWidth;
        this.destHeight = destHeight;
        this.pad_x = pad_x;
        this.pad_y = pad_y;
    }
}

function padSprite(sprite, paddingConfig)
{
    let spriteWidth = sprite[0].length;
    let spriteHeight = sprite.length;

    let destWidth = paddingConfig.destWidth != -1 ? paddingConfig.destWidth : spriteWidth;
    let destHeight = paddingConfig.destHeight != -1 ? paddingConfig.destHeight : spriteHeight;
    let pad_x = paddingConfig.pad_x;
    let pad_y = paddingConfig.pad_y;

    if (spriteWidth > destWidth || spriteHeight > destHeight && destHeight != -1)
    {
        console.log("ERROR: destSize is smaller than current size");
        return sprite;
    }

    let data = [];

    let totalXpadding = destWidth - spriteWidth;
    let totalYpadding = destHeight - spriteHeight;

    let paddingRight_01 = pad_x + 0.5 - pad_x * 0.5; // 0, 0.5, 1
    let paddingTop_01 = pad_y + 0.5 - pad_y * 0.5; // 0, 0.5, 1

    let paddingRight = Math.round(paddingRight_01 * totalXpadding);
    let paddingTop = Math.round(paddingTop_01 * totalYpadding);
    let paddingLeft = totalXpadding - paddingRight;
    let paddingBottom = totalYpadding - paddingTop;

    for (let y = 0; y < destHeight; y++)
    {
        data.push([]);
        for (let x = 0; x < destWidth; x++)
        {
            if (x < paddingLeft || x >= destWidth - paddingRight || y < paddingTop || y >= destHeight - paddingBottom)
                data[y].push([0, 0, 0, 0]);
            else
                data[y].push(sprite[y - paddingTop][x - paddingLeft]);
        }
    }
    
    return data;
}

let wallSprite;
let floorSprite;
let ceilingSprite;

let statusBarSprite;
let weaponFrameSprite;

let fireBulletSprite;
let playerSprite;

let handgunSprite;
let shotgunSprite;
let machinegunSprite;

let opponentSprite;
let corpseSprite;

let font;


async function spriteReader_init()
{
    weaponImageBounds = [200, 102];
    let weaponImagePaddingConfig = new PaddingConfig(weaponImageBounds[0], weaponImageBounds[1], 0, 1);


    let inits = 0;
    const initCount = 12;

    spriteReader_getSpriteString('rrock10',                 (img) => { wallSprite = new Sprite(img, 0.5, 0.66); inits++; });
    spriteReader_getSpriteString('floor5_1',                 (img) => { floorSprite = new Sprite(img, 1, 1); inits++; })
    spriteReader_getSpriteString('ceil3_5',                 (img) => { ceilingSprite = new Sprite(img, 2, 2); inits++; })

    spriteReader_getSpriteString('StatusBar_Doom_Own',  (img) => { statusBarSprite = new Sprite(img, 1, 1); inits++; });
    spriteReader_getSpriteString('WeaponFrame',         (img) => { weaponFrameSprite = new Sprite(img, 1, 1); inits++ });

    spriteReader_getSpriteString('FireBullet',            (img) =>
    {
        let paddingConfig = new PaddingConfig(-1, 120, 0, -0.2);
        fireBulletSprite = new SpriteSet(img,
            [
                new Still('Idle_S', 0, 0, 34, 33, paddingConfig),
                new Still('Idle_SW', 0, 34, 56, 28, paddingConfig),
                new Still('Idle_W', 0, 62, 67, 25, paddingConfig),
                new Still('Idle_NW', 0, 89, 54, 26, paddingConfig),
                new Still('Idle_N', 0, 115, 28, 30, paddingConfig),
                new Still('Idle_NE', 0, 145, 54, 26, paddingConfig),
                new Still('Idle_E', 0, 171, 67, 25, paddingConfig),
                new Still('Idle_SE', 0, 198, 56, 28, paddingConfig)
            ],
            [
                new StillSequence('Fly_S',
                [
                    new Still(0, 0, 0, 34, 33, paddingConfig),
                    new Still(0, 34, 0, 33, 33, paddingConfig)
                ]),
                new StillSequence('Fly_SW',
                [
                    new Still(0, 0, 34, 56, 28, paddingConfig),
                    new Still(0, 56, 34, 51, 28, paddingConfig)
                ]),
                new StillSequence('Fly_W',
                [
                    new Still(0, 0, 62, 67, 25, paddingConfig),
                    new Still(0, 67, 62, 62, 27, paddingConfig)
                ]),
                new StillSequence('Fly_NW',
                [
                    new Still(0, 0, 89, 54, 26, paddingConfig),
                    new Still(0, 54, 89, 46, 26, paddingConfig)
                ]),
                new StillSequence('Fly_N',
                [
                    new Still(0, 0, 115, 28, 30, paddingConfig),
                    new Still(0, 28, 115, 25, 27, paddingConfig)
                ]),
                new StillSequence('Fly_NE',
                [
                    new Still(0, 0, 145, 54, 26, paddingConfig),
                    new Still(0, 54, 145, 46, 27, paddingConfig)
                ]),
                new StillSequence('Fly_E',
                [
                    new Still(0, 0, 171, 67, 25, paddingConfig),
                    new Still(0, 67, 171, 62, 27, paddingConfig)
                ]),
                new StillSequence('Fly_SE',
                [
                    new Still(0, 0, 198, 56, 28, paddingConfig),
                    new Still(0, 56, 198, 51, 28, paddingConfig)
                ])
            ],
            false
        );
        inits++;
    });

    spriteReader_getSpriteString('DoomGuy', (img) =>
    {
        // ToDo: Remove paddingConfig, should not be needed
        let paddingConfig = new PaddingConfig(38, 56, 0, 1);
        playerSprite = new SpriteSet(img,
            [
                new Still('Idle_S', 0, 0, 36, 56, paddingConfig),
                new Still('Idle_SW', 0, 56, 26, 56, paddingConfig),
                new Still('Idle_W', 0, 112, 29, 56, paddingConfig),
                new Still('Idle_NW', 0, 168, 29, 55, paddingConfig),
                new Still('Idle_N', 0, 224, 38, 56, paddingConfig),
                new Still('Idle_NE', 0, 280, 29, 55, paddingConfig),
                new Still('Idle_E', 0, 336, 29, 56, paddingConfig),
                new Still('Idle_SE', 0, 392, 26, 56, paddingConfig)
            ],
            [
                new StillSequence('Walk_S',
                [
                    new Still(0, 0, 0, 36, 56),
                    new Still(0, 36, 0, 36, 56),
                    new Still(0, 72, 0, 36, 56),
                    new Still(0, 108, 0, 35, 56)
                ]),
                new StillSequence('Walk_SW',
                [
                    new Still(0, 0, 56, 26, 56),
                    new Still(0, 26, 56, 33, 56),
                    new Still(0, 59, 56, 26, 56),
                    new Still(0, 85, 56, 31, 56)
                ]),
                new StillSequence('Walk_W',
                [
                    new Still(0, 0, 112, 29, 56),
                    new Still(0, 29, 112, 42, 56),
                    new Still(0, 70, 112, 29, 56),
                    new Still(0, 99, 112, 39, 55)
                ]),
                new StillSequence('Walk_NW',
                [
                    new Still(0, 168, 29, 55),
                    new Still(0, 29, 168, 37, 56),
                    new Still(0, 66, 168, 29, 56),
                    new Still(0, 95, 167, 37, 56)
                ]),
                new StillSequence('Walk_N',
                [
                    new Still(0, 0, 224, 38, 56),
                    new Still(0, 38, 224, 34, 56),
                    new Still(0, 72, 224, 35, 56),
                    new Still(0, 107, 224, 34, 56)
                ]),
                new StillSequence('Walk_NE',
                [
                    new Still(0, 0, 280, 29, 55),
                    new Still(0, 29, 280, 37, 56),
                    new Still(0, 66, 280, 29, 56),
                    new Still(0, 95, 280, 37, 56)
                ]),
                new StillSequence('Walk_E',
                [
                    new Still(0, 0, 336, 29, 56),
                    new Still(0, 29, 336, 41, 56),
                    new Still(0, 70, 336, 29, 56),
                    new Still(0, 99, 336, 39, 56)
                ]),
                new StillSequence('Walk_SE',
                [
                    new Still(0, 0, 392, 26, 56),
                    new Still(0, 26, 392, 33, 56),
                    new Still(0, 59, 392, 26, 56),
                    new Still(0, 85, 392, 31, 56)
                ])
            ],
            false
        );
        inits++;
    });

    
    spriteReader_getSpriteString('Shotgun', (img) =>
    {
        shotgunSprite = new SpriteSet(img,
            [
                new Still('Idle', 0, 39, 91, 63, weaponImagePaddingConfig)
            ],
            [
                new StillSequence('Shoot',
                [
                    new Still(1, 91, 22, 91, 80, weaponImagePaddingConfig),
                    new Still(2, 0 + 91 * 2, 6, 91, 96, weaponImagePaddingConfig),
                    new Still(3, 91 + 91 * 2, 0, 92, 102, weaponImagePaddingConfig),
                    new Still(4, 183 + 91 * 2, 24, 93, 78, weaponImagePaddingConfig),
                    new Still(5, 276 + 91 * 2, 74, 200, 28, weaponImagePaddingConfig),
                    new Still(6, 476 + 91 * 2, 32, 164, 70, weaponImagePaddingConfig),
                    new Still(7, 640 + 91 * 2, 45, 125, 57, weaponImagePaddingConfig),
                    new Still(8, 765 + 91 * 2, 68, 87, 34, weaponImagePaddingConfig),
                    new Still(9, 1034, 24, 93, 78, weaponImagePaddingConfig),
                    new Still(10, 0, 39, 91, 63, weaponImagePaddingConfig), // First Image
                    new Still(11, 0, 39, 91, 63, weaponImagePaddingConfig),
                    new Still(10, 0, 39, 91, 63, weaponImagePaddingConfig),
                    new Still(10, 0, 39, 91, 63, weaponImagePaddingConfig)
                ])
            ],
            true
        );
        inits++;
    });

    spriteReader_getSpriteString('Chaingun', (img) =>
    {
        machinegunSprite = new SpriteSet(img,
            [
                new Still('Idle', 0, 0, 110, 54, weaponImagePaddingConfig)
            ],
            [
                new StillSequence('Shoot',
                [
                    new Still(1, 110, 0, 110, 85, weaponImagePaddingConfig),
                    new Still(2, 220, 15, 110, 70, weaponImagePaddingConfig)
                ])
            ],
            true
        );
        inits++;
    });

    spriteReader_getSpriteString('Handgun', (img) =>
    {
        handgunSprite = new SpriteSet(img,
            [
                new Still('Idle', 0, 23, 50, 64, weaponImagePaddingConfig)
            ],
            [
                new StillSequence('Shoot',
                [
                    new Still(1, 50, 0, 52, 102, weaponImagePaddingConfig),
                    new Still(2, 102, 7, 50, 80, weaponImagePaddingConfig),
                    new Still(3, 152, 3, 51, 84, weaponImagePaddingConfig),
                    new Still(4, 203, 0, 51, 87, weaponImagePaddingConfig),
                    new Still(5, 0, 23, 50, 64, weaponImagePaddingConfig) // First Image
                ])
            ],
            true
        );
        inits++;
    });

    
    spriteReader_getSpriteString('Corpse', (img) =>
    {
        let paddingConfig = new PaddingConfig(53, 56, 0, -1);
        corpseSprite = new SpriteSet(img,
            [
                new Still('Idle', 373, 0, 53, 16, paddingConfig) // Last Sprite of Animation
            ],
            [
                new StillSequence('Explode',
                [
                    //new Still(0, 0, 0, 38, 56, paddingConfig),
                    new Still(1, 38, 0, 41, 53, paddingConfig),
                    new Still(2, 79, 0, 44, 49, paddingConfig),
                    new Still(3, 123, 0, 46, 45, paddingConfig),
                    new Still(4, 169, 0, 49, 39, paddingConfig),
                    new Still(5, 218, 0, 49, 35, paddingConfig),
                    new Still(6, 267, 0, 53, 27, paddingConfig),
                    new Still(7, 310, 0, 53, 16, paddingConfig),
                    new Still(8, 373, 0, 53, 16, paddingConfig)
                ])
            ],
            false
        );
        inits++;
    })

    spriteReader_getSpriteString('Font_Denex', (img) =>
    {
        font = new Font(img,
            [
                new Still(' ', 1, 1, 9, 15),
                new Still('!', 11, 1, 5, 15),
                new Still('%', 53, 1, 13, 15),
                new Still('0', 1, 17, 15, 15),
                new Still('1', 17, 17, 8, 15),
                new Still('2', 26, 17, 11, 15),
                new Still('3', 39, 17, 11, 15),
                new Still('4', 51, 17, 13, 15),
                new Still('5', 65, 17, 12, 15),
                new Still('6', 78, 17, 13, 15),
                new Still('7', 92, 17, 14, 15),
                new Still('8', 107, 17, 12, 15),
                new Still('9', 120, 17, 13, 15)
                //new Subsprite(''),
            ],
            [],
            true
        );
        inits++;
    });


    // Check each checkIntervall ms whether all ressources are loaded now
    const checkIntervall = 50;
    while(inits != initCount)
        await new Promise(resolve => setTimeout(resolve, checkIntervall));
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