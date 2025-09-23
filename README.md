# Photo Watermark CLI Tool

This tool adds a text watermark with the capture date (extracted from EXIF data) to images. Users can customize the font size, color, and position of the watermark.

## Features

- Extracts capture date from image EXIF data
- Adds customizable text watermark (font size, color, position)
- Saves watermarked images to a new directory
- Command-line interface for easy use

## Requirements

- Python 3.x
- Pillow (PIL) library

Install the required library with:
```bash
pip install Pillow
```

## Usage

```bash
python photowatermark.py <image_path> [options]
```

### Arguments

- `image_path`: Path to the image file

### Options

- `--font-size`: Font size for the watermark (default: 20)
- `--color`: Watermark color as RGB values (default: 255 255 255)
- `--position`: Position of the watermark (default: bottom-right)

Position options:
- top-left
- top-center
- top-right
- center
- bottom-left
- bottom-center
- bottom-right

### Example

```bash
python photowatermark.py photo.jpg --font-size 30 --color 255 0 0 --position bottom-right
```

This will add a red watermark with font size 30 at the bottom-right corner of the image.