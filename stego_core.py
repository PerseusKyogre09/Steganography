from PIL import Image
import struct
import zlib

EOF_MARKER_BYTES = b'\xAA\xBB\xCC\xDD\xEE\xFF'

BITS_PER_CHANNEL = 2  

def to_binary(data):
    """Convert bytes to a binary string"""
    return ''.join(f'{byte:08b}' for byte in data)

def from_binary(bin_str):
    if len(bin_str) % 8 != 0:
        bin_str = bin_str + '0' * (8 - (len(bin_str) % 8))
    return bytes(int(bin_str[i:i+8], 2) for i in range(0, len(bin_str), 8))

def encode_data_to_image(image_path, data_bytes, output_path, compress=True):
    if compress:
        data_bytes = zlib.compress(data_bytes, level=9)
        
    data_with_marker = data_bytes + EOF_MARKER_BYTES
    
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    
    max_bytes = (width * height * 3 * BITS_PER_CHANNEL) // 8
    data_size = len(data_with_marker)
    
    if data_size > max_bytes:
        raise ValueError(f"Data too large ({data_size} bytes) for this image (max {max_bytes} bytes). Try using a larger image.")
    
    bin_data = to_binary(data_with_marker)
    data_index = 0
    modified = img.copy()
    pixels = modified.load()
    
    mask = (1 << BITS_PER_CHANNEL) - 1
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            if data_index + BITS_PER_CHANNEL <= len(bin_data):
                bits = int(bin_data[data_index:data_index + BITS_PER_CHANNEL], 2)
                r = (r & ~mask) | bits
                data_index += BITS_PER_CHANNEL
            
            if data_index + BITS_PER_CHANNEL <= len(bin_data):
                bits = int(bin_data[data_index:data_index + BITS_PER_CHANNEL], 2)
                g = (g & ~mask) | bits
                data_index += BITS_PER_CHANNEL
            
            if data_index + BITS_PER_CHANNEL <= len(bin_data):
                bits = int(bin_data[data_index:data_index + BITS_PER_CHANNEL], 2)
                b = (b & ~mask) | bits
                data_index += BITS_PER_CHANNEL
                
            pixels[x, y] = (r, g, b)
            
            if data_index >= len(bin_data):
                break
        
        if data_index >= len(bin_data):
            break
    
    modified.save(output_path, "PNG")

def decode_data_from_image(image_path):
    """Decode data from an image using enhanced steganography"""
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    pixels = img.load()
    
    mask = (1 << BITS_PER_CHANNEL) - 1
    
    bits = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            bits.extend([str((r & mask) >> i) for i in range(BITS_PER_CHANNEL-1, -1, -1)])
            bits.extend([str((g & mask) >> i) for i in range(BITS_PER_CHANNEL-1, -1, -1)])
            bits.extend([str((b & mask) >> i) for i in range(BITS_PER_CHANNEL-1, -1, -1)])
    
    binary_data = ''.join(bits)
    
    all_bytes = from_binary(binary_data)
    
    marker_pos = all_bytes.find(EOF_MARKER_BYTES)
    if marker_pos != -1:
        data = all_bytes[:marker_pos]
        
        try:
            return zlib.decompress(data)
        except zlib.error:
            return data
    else:
        return all_bytes
