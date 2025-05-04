from PIL import Image
import struct
import zlib
import time

# Using a binary EOF marker
EOF_MARKER_BYTES = b'\xAA\xBB\xCC\xDD\xEE\xFF'

# Number of bits to use per color channel 
BITS_PER_CHANNEL = 1

def to_binary(data):
    """Convert bytes to a binary string"""
    return ''.join(f'{byte:08b}' for byte in data)

def from_binary(bin_str):
    if len(bin_str) % 8 != 0:
        bin_str = bin_str + '0' * (8 - (len(bin_str) % 8))
    return bytes(int(bin_str[i:i+8], 2) for i in range(0, len(bin_str), 8))

def encode_data_to_image(image_path, data_bytes, output_path, compress=True):
    if compress:
        try:
            data_bytes = zlib.compress(data_bytes, level=9)
        except Exception as e:
            print(f"Compression error: {e}")
            # Continue without compression if it fails
            pass
        
    data_with_marker = data_bytes + EOF_MARKER_BYTES
    
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    
    max_bytes = (width * height * 3 * BITS_PER_CHANNEL) // 8
    data_size = len(data_with_marker)
    
    if data_size > max_bytes:
        raise ValueError(f"Data too large ({data_size} bytes) for this image (max {max_bytes} bytes). Try using a larger image.")
    
    # Convert data to binary string
    bin_data = to_binary(data_with_marker)
    data_index = 0
    modified = img.copy()
    pixels = modified.load()
    
    mask = (1 << BITS_PER_CHANNEL) - 1
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            if data_index < len(bin_data):
                bit = int(bin_data[data_index])
                r = (r & ~mask) | bit
                data_index += 1
            
            if data_index < len(bin_data):
                bit = int(bin_data[data_index])
                g = (g & ~mask) | bit
                data_index += 1
            
            if data_index < len(bin_data):
                bit = int(bin_data[data_index])
                b = (b & ~mask) | bit
                data_index += 1
                
            pixels[x, y] = (r, g, b)
            
            if data_index >= len(bin_data):
                break
        if data_index >= len(bin_data):
            break
    
    # Save the modified image
    modified.save(output_path, "PNG")

def decode_data_from_image(image_path):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    pixels = img.load()
    
    mask = (1 << BITS_PER_CHANNEL) - 1
    
    binary_string = ""
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            binary_string += str(r & 1)
            binary_string += str(g & 1)
            binary_string += str(b & 1)
                
            # Check for EOF marker periodically
            if len(binary_string) % 1024 == 0:
                # Convert current chunk to bytes
                if len(binary_string) % 8 != 0:
                    padded_binary = binary_string + '0' * (8 - (len(binary_string) % 8))
                else:
                    padded_binary = binary_string
                
                temp_bytes = from_binary(padded_binary)
                # Check if EOF marker is in the current data
                if EOF_MARKER_BYTES in temp_bytes:
                    # Found the marker, no need to process more pixels
                    all_bytes = from_binary(binary_string[:len(binary_string) - (len(binary_string) % 8)])
                    marker_pos = all_bytes.find(EOF_MARKER_BYTES)
                    data = all_bytes[:marker_pos]
                    
                    try:
                        return zlib.decompress(data)
                    except zlib.error:
                        # If decompression fails, return the raw data
                        return data
    
    if len(binary_string) % 8 != 0:
        binary_string = binary_string + '0' * (8 - (len(binary_string) % 8))
    
    all_bytes = from_binary(binary_string)
    
    # Find the EOF marker
    marker_pos = all_bytes.find(EOF_MARKER_BYTES)
    if marker_pos != -1:
        # Get the data without the EOF marker
        data = all_bytes[:marker_pos]
        try:
            return zlib.decompress(data)
        except zlib.error:
            # If decompression fails, return the raw data
            return data
    else:
        # If no marker found, return all the data
        return all_bytes
