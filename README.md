# Steganography

Steganography is a steganography tool that allows you to hide messages or files inside PNG images. It offers both a Python desktop application and a web-based version for maximum flexibility.

## Overview

Steganography is the practice of concealing information within other non-secret data or a physical object. It uses Least Significant Bit (LSB) steganography to hide data in images by modifying the least significant bits of the color channels in each pixel, making the changes virtually imperceptible to the human eye.

## Project Components

This project consists of two implementations:

1. **Python Desktop Application** - A GUI-based desktop application
2. **Web Application** - A browser-based version with the same functionality

## Python Desktop Application

### Requirements

- Python 3.6+
- Dependencies:
  - CustomTkinter
  - Pillow (PIL)
  - Standard Python libraries (os, struct, threading, queue)
- Install requirements by running
```bash
pip install -r requirements.txt
```

### Files

- `main.py` - Entry point for the desktop application
- `gui.py` - GUI implementation using CustomTkinter
- `stego_core.py` - Core steganography implementation

### Features

- Modern dark-themed UI with tabs for encoding and decoding
- Hide text messages inside PNG images
- Hide any file type inside PNG images
- Preview images before encoding/decoding
- Display capacity information
- Decode automatically detects whether text or files are hidden
- Multi-threaded processing for responsiveness

### Running the Desktop Application

```
python main.py
```

## Web Application

A client-side web version of the Steganography tool with all the same functionality as the desktop version.

### Files

- `index.html` - Main HTML structure and UI
- `css/style.css` - Styling and theming
- `js/stego.js` - Core steganography functionality in JavaScript
- `js/main.js` - UI interaction and application logic

### Features

- Same functionality as the Python version
- Client-side processing (all operations happen in your browser)
- No data is ever uploaded to a server
- Cross-platform compatibility with modern browsers
- Responsive design for both desktop and mobile

### Using the Web Version

1. Open [Steganography](https://perseuskyogre09.github.io/Steganography/) in any modern web browser
2. No installation required!

## How Steganography Works

1. **Encoding**:
   - The image pixels are accessed through RGB channels
   - The least significant bit(s) of each color channel are replaced with bits from the data
   - An EOF marker is appended to the data for reliable extraction
   - Data is optionally compressed to save space
   - Special markers differentiate between text and file data

2. **Decoding**:
   - The least significant bit(s) of each pixel's color channels are extracted
   - The process continues until the EOF marker is found
   - Data is decompressed if necessary
   - The type marker determines if it's text or a file
   - For files, the extension is preserved for proper opening

## Privacy & Security

- Both implementations process all data locally
- No data is ever sent to any server
- Your messages and files remain private
- The web application works offline after initial load

## Limitations

- Only PNG images are supported (to avoid data loss from compression)
- Larger files require larger cover images
- The encoded image must be saved as PNG (other formats will lose the hidden data)
- Heavy compression or image editing will corrupt the hidden data

## Browser Compatibility

The web version works with all modern browsers including:
- Chrome 88+
- Firefox 90+
- Safari 14+
- Edge 88+

## License

MIT License - Feel free to use, modify, and distribute!