/**
 ** Steganography Core Library
 * JavaScript implementation of steganography functions
 */

// Constants
const EOF_MARKER = new Uint8Array([0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]);
const BITS_PER_CHANNEL = 1;
const TEXT_TYPE = new TextEncoder().encode('TXT:');
const FILE_TYPE = new TextEncoder().encode('FILE:');

// Append one array to another
function concatArrays(...arrays) {
    let totalLength = arrays.reduce((acc, arr) => acc + arr.length, 0);
    let result = new Uint8Array(totalLength);
    let offset = 0;
    for (let arr of arrays) {
        result.set(arr, offset);
        offset += arr.length;
    }
    return result;
}

// Convert a string to binary representation
function stringToBinary(str) {
    const encoder = new TextEncoder();
    const bytes = encoder.encode(str);
    return Array.from(bytes).map(byte => 
        byte.toString(2).padStart(8, '0')
    ).join('');
}

// Convert binary string to Uint8Array
function binaryToUint8Array(binary) {
    const bytes = [];
    for (let i = 0; i < binary.length; i += 8) {
        if (i + 8 <= binary.length) {
            bytes.push(parseInt(binary.substr(i, 8), 2));
        } else {
            const lastBits = binary.substr(i);
            bytes.push(parseInt(lastBits.padEnd(8, '0'), 2));
        }
    }
    return new Uint8Array(bytes);
}

// Compress data using zlib
async function compressData(data) {
    try {
        const ds = new DeflateStream();
        const compressedChunks = [];
        
        ds.write(data);
        ds.end();
        
        for await (const chunk of ds) {
            compressedChunks.push(chunk);
        }
        
        const totalLength = compressedChunks.reduce((acc, chunk) => acc + chunk.length, 0);
        const compressedData = new Uint8Array(totalLength);
        let offset = 0;
        
        for (const chunk of compressedChunks) {
            compressedData.set(chunk, offset);
            offset += chunk.length;
        }
        
        return compressedData;
    } catch (e) {
        console.error('Compression error:', e);
        return data;
    }
}

// Decompress data using zlib
async function decompressData(data) {
    try {
        const is = new InflateStream();
        const decompressedChunks = [];
        
        is.write(data);
        is.end();
        
        for await (const chunk of is) {
            decompressedChunks.push(chunk);
        }
        
        const totalLength = decompressedChunks.reduce((acc, chunk) => acc + chunk.length, 0);
        const decompressedData = new Uint8Array(totalLength);
        let offset = 0;
        
        for (const chunk of decompressedChunks) {
            decompressedData.set(chunk, offset);
            offset += chunk.length;
        }
        
        return decompressedData;
    } catch (e) {
        console.error('Decompression error:', e);
        return data;
    }
}

class DeflateStream extends TransformStream {
    constructor() {
        let controller;
        super({
            start(c) {
                controller = c;
            },
            transform(chunk, controller) {
                const compressedChunk = chunk;
                controller.enqueue(compressedChunk);
            }
        });
        
        this.controller = controller;
    }
    
    write(chunk) {
        this.controller.enqueue(chunk);
    }
    
    end() {
        this.controller.terminate();
    }
}

class InflateStream extends TransformStream {
    constructor() {
        let controller;
        super({
            start(c) {
                controller = c;
            },
            transform(chunk, controller) {
                const decompressedChunk = chunk;
                controller.enqueue(decompressedChunk);
            }
        });
        
        this.controller = controller;
    }
    
    write(chunk) {
        this.controller.enqueue(chunk);
    }
    
    end() {
        this.controller.terminate();
    }
}

// Use browser's compression API
if (typeof CompressionStream !== 'undefined') {
    DeflateStream = function() {
        return new CompressionStream('deflate');
    };
    
    InflateStream = function() {
        return new DecompressionStream('deflate');
    };
}

async function encodeDataToImage(image, data, compress = true) {
    return new Promise(async (resolve, reject) => {
        try {
            // Draw the original image
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = image.width;
            canvas.height = image.height;
            ctx.drawImage(image, 0, 0);
            
            // Get image data
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const pixels = imageData.data;
            
            // Calculate max capacity
            const maxBytes = Math.floor((canvas.width * canvas.height * 3 * BITS_PER_CHANNEL) / 8);
            
            // Compress data if requested
            let dataToEncode = compress ? await compressData(data) : data;
            
            // Add EOF marker
            dataToEncode = concatArrays(dataToEncode, EOF_MARKER);
            
            // Check if data fits
            if (dataToEncode.length > maxBytes) {
                reject(new Error(`Data too large (${dataToEncode.length} bytes) for this image (max ${maxBytes} bytes). Try using a larger image.`));
                return;
            }
            
            // Convert data to binary string
            let binaryData = '';
            for (let i = 0; i < dataToEncode.length; i++) {
                binaryData += dataToEncode[i].toString(2).padStart(8, '0');
            }
            
            // Set mask for LSB
            const mask = (1 << BITS_PER_CHANNEL) - 1;
            
            // Encode data into image pixels
            let dataIndex = 0;
            
            for (let i = 0; i < pixels.length; i += 4) {
                // Red channel
                if (dataIndex < binaryData.length) {
                    const bit = parseInt(binaryData[dataIndex]);
                    pixels[i] = (pixels[i] & ~mask) | bit;
                    dataIndex++;
                }
                // Green channel
                if (dataIndex < binaryData.length) {
                    const bit = parseInt(binaryData[dataIndex]);
                    pixels[i + 1] = (pixels[i + 1] & ~mask) | bit;
                    dataIndex++;
                }
                // Blue channel
                if (dataIndex < binaryData.length) {
                    const bit = parseInt(binaryData[dataIndex]);
                    pixels[i + 2] = (pixels[i + 2] & ~mask) | bit;
                    dataIndex++;
                }
                // Break if all data encoded
                if (dataIndex >= binaryData.length) {
                    break;
                }
            }
            // Put modified pixels back to canvas
            ctx.putImageData(imageData, 0, 0);
            canvas.toBlob(blob => {
                resolve(blob);
            }, 'image/png');
            
        } catch (error) {
            reject(error);
        }
    });
}
async function decodeDataFromImage(image) {
    return new Promise((resolve, reject) => {
        try {
            // Create a canvas and draw the image
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = image.width;
            canvas.height = image.height;
            ctx.drawImage(image, 0, 0);
            
            // Get image data
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const pixels = imageData.data;
            
            // Set mask for LSB
            const mask = (1 << BITS_PER_CHANNEL) - 1;
            
            // Extract binary data
            let binaryString = '';
            
            // Extract bits from each color channel
            for (let i = 0; i < pixels.length; i += 4) {
                // Extract from red channel
                binaryString += (pixels[i] & mask).toString();
                // Extract from green channel
                binaryString += (pixels[i + 1] & mask).toString();
                // Extract from blue channel
                binaryString += (pixels[i + 2] & mask).toString();
                // Check for EOF marker periodically
                if (binaryString.length % 1024 === 0) {
                    const paddedBinary = binaryString.length % 8 !== 0 ?
                        binaryString + '0'.repeat(8 - (binaryString.length % 8)) : binaryString;
                    
                    const tempBytes = binaryToUint8Array(paddedBinary);
                    if (findMarker(tempBytes, EOF_MARKER) !== -1) {
                        const allBytes = binaryToUint8Array(binaryString.substring(0, binaryString.length - (binaryString.length % 8)));
                        const markerPos = findMarker(allBytes, EOF_MARKER);
                        
                        if (markerPos !== -1) {
                            const extractedData = allBytes.slice(0, markerPos);
                            
                            // Decompress the data
                            decompressData(extractedData)
                                .then(result => resolve(result))
                                .catch(() => resolve(extractedData));
                            return;
                        }
                    }
                }
            }
            
            if (binaryString.length % 8 !== 0) {
                binaryString += '0'.repeat(8 - (binaryString.length % 8));
            }
            
            const allBytes = binaryToUint8Array(binaryString);
            const markerPos = findMarker(allBytes, EOF_MARKER);
            
            if (markerPos !== -1) {
                const extractedData = allBytes.slice(0, markerPos);
                
                // Decompress the data
                decompressData(extractedData)
                    .then(result => resolve(result))
                    .catch(() => resolve(extractedData));
            } else {
                resolve(allBytes);
            }
            
        } catch (error) {
            reject(error);
        }
    });
}
function findMarker(data, marker) {
    for (let i = 0; i <= data.length - marker.length; i++) {
        let found = true;
        for (let j = 0; j < marker.length; j++) {
            if (data[i + j] !== marker[j]) {
                found = false;
                break;
            }
        }
        if (found) {
            return i;
        }
    }
    return -1;
}


function prepareTextData(text) {
    const textEncoder = new TextEncoder();
    const textBytes = textEncoder.encode(text);
    return concatArrays(TEXT_TYPE, textBytes);
}
async function prepareFileData(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const fileData = new Uint8Array(e.target.result);
                const extension = file.name.split('.').pop();
                const extensionBytes = new TextEncoder().encode(extension);
                
                // Pack extension length as a 2-byte integer
                const extLenBytes = new Uint8Array(2);
                extLenBytes[0] = (extensionBytes.length >> 8) & 0xFF;
                extLenBytes[1] = extensionBytes.length & 0xFF;
                
                // Combine all parts
                const preparedData = concatArrays(
                    FILE_TYPE,
                    extLenBytes,
                    extensionBytes,
                    fileData
                );
                
                resolve(preparedData);
            } catch (error) {
                reject(error);
            }
        };
        reader.onerror = function() {
            reject(new Error('Error reading file'));
        };
        reader.readAsArrayBuffer(file);
    });
}


function processDecodedData(data) {
    if (startsWithArray(data, TEXT_TYPE)) {
        const textData = data.slice(TEXT_TYPE.length);
        const decoder = new TextDecoder();
        return {
            type: 'text',
            content: decoder.decode(textData)
        };
    }
    
    // Check for file marker
    if (startsWithArray(data, FILE_TYPE)) {
        const fileData = data.slice(FILE_TYPE.length);
        
        // Extract extension length
        const extLen = (fileData[0] << 8) | fileData[1];
        
        // Extract extension
        const extensionBytes = fileData.slice(2, 2 + extLen);
        const decoder = new TextDecoder();
        const extension = decoder.decode(extensionBytes);
        
        // Extract file content
        const content = fileData.slice(2 + extLen);
        
        return {
            type: 'file',
            extension: extension,
            content: content
        };
    }
    
    // Unknown format
    try {
        const decoder = new TextDecoder();
        const text = decoder.decode(data);
        return {
            type: 'text',
            content: text
        };
    } catch (e) {
        return {
            type: 'binary',
            content: data
        };
    }
}

function startsWithArray(data, prefix) {
    if (data.length < prefix.length) {
        return false;
    }
    
    for (let i = 0; i < prefix.length; i++) {
        if (data[i] !== prefix[i]) {
            return false;
        }
    }
    
    return true;
}

function downloadDecodedFile(data, extension) {
    const blob = new Blob([data]);
    const url = URL.createObjectURL(blob);
    const filename = `decoded_file.${extension}`;
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
}