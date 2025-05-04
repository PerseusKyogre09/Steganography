from PIL import Image
import struct
import zlib  # For compression

# Using a binary EOF marker to avoid text/binary confusion
EOF_MARKER_BYTES = b'\xAA\xBB\xCC\xDD\xEE\xFF'

# Number of bits to use per color channel (increasing this increases capacity)
BITS_PER_CHANNEL = 2  # Using 2 bits instead of 1

def to_binary(data):
    """Convert bytes to a binary string"""
    return ''.join(f'{byte:08b}' for byte in data)

def from_binary(bin_str):
    """Convert a binary string back to bytes"""
    # Ensure the binary string length is a multiple of 8
    if len(bin_str) % 8 != 0:
        bin_str = bin_str + '0' * (8 - (len(bin_str) % 8))
    return bytes(int(bin_str[i:i+8], 2) for i in range(0, len(bin_str), 8))

def encode_data_to_image(image_path, data_bytes, output_path, compress=True):
    """Encode data into an image using enhanced steganography"""
    # Optionally compress the data to increase capacity
    if compress:
        data_bytes = zlib.compress(data_bytes, level=9)
        
    # Add EOF marker to know where the data ends
    data_with_marker = data_bytes + EOF_MARKER_BYTES
    
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    
    # Calculate the increased capacity with higher bits per channel
    max_bytes = (width * height * 3 * BITS_PER_CHANNEL) // 8
    data_size = len(data_with_marker)
    
    if data_size > max_bytes:
        raise ValueError(f"Data too large ({data_size} bytes) for this image (max {max_bytes} bytes). Try using a larger image.")
    
    # Convert data to binary string
    bin_data = to_binary(data_with_marker)
    data_index = 0
    modified = img.copy()
    pixels = modified.load()
    
    # Create a bitmask based on BITS_PER_CHANNEL
    mask = (1 << BITS_PER_CHANNEL) - 1  # e.g., 0b11 for 2 bits
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            if data_index + BITS_PER_CHANNEL <= len(bin_data):
                # Extract bits to encode
                bits = int(bin_data[data_index:data_index + BITS_PER_CHANNEL], 2)
                # Clear the lowest BITS_PER_CHANNEL bits and set them to our data bits
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
            
            # Check if we've embedded all the data
            if data_index >= len(bin_data):
                break
        
        # Also break outer loop if done
        if data_index >= len(bin_data):
            break
    
    # Save the modified image
    modified.save(output_path, "PNG")

def decode_data_from_image(image_path):
    """Decode data from an image using enhanced steganography"""
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    pixels = img.load()
    
    # Create a bitmask based on BITS_PER_CHANNEL
    mask = (1 << BITS_PER_CHANNEL) - 1  # e.g., 0b11 for 2 bits
    
    # Extract the bits from each color channel
    bits = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            # Extract BITS_PER_CHANNEL bits from each channel
            bits.extend([str((r & mask) >> i) for i in range(BITS_PER_CHANNEL-1, -1, -1)])
            bits.extend([str((g & mask) >> i) for i in range(BITS_PER_CHANNEL-1, -1, -1)])
            bits.extend([str((b & mask) >> i) for i in range(BITS_PER_CHANNEL-1, -1, -1)])
    
    # Convert the binary array to a string
    binary_data = ''.join(bits)
    
    # Convert the binary string to bytes
    all_bytes = from_binary(binary_data)
    
    # Find the EOF marker
    marker_pos = all_bytes.find(EOF_MARKER_BYTES)
    if marker_pos != -1:
        # Get the data without the EOF marker
        data = all_bytes[:marker_pos]
        
        # Try to decompress (assuming it was compressed)
        try:
            return zlib.decompress(data)
        except zlib.error:
            # If decompression fails, return the raw data
            return data
    else:
        # If no marker found, return all the data (might be corrupted)
        return all_bytes
