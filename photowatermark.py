#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Photo Watermark CLI Tool
========================

This tool adds a text watermark with the capture date (extracted from EXIF data)
to images. Users can customize the font size, color, and position of the watermark.
"""

import argparse
import os
from PIL import Image, ExifTags
from PIL.ImageDraw import ImageDraw
from PIL.ImageFont import truetype
import datetime

def get_exif_data(image_path):
    """Extract EXIF data from an image file."""
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if exif_data is not None:
            # Convert EXIF tags to human-readable format
            exif = {
                ExifTags.TAGS.get(tag, tag): value
                for tag, value in exif_data.items()
                if tag in ExifTags.TAGS
            }
            return exif
    except Exception as e:
        print(f"Error reading EXIF data from {image_path}: {e}")
    return {}

def get_capture_date(exif_data):
    """Extract capture date from EXIF data."""
    date_str = exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
    if date_str:
        try:
            # Parse the date string (typically in format 'YYYY:MM:DD HH:MM:SS')
            dt = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
    return None

def add_watermark(image_path, output_path, text, font_size=20, color=(255, 255, 255), position='bottom-right'):
    """Add a text watermark to an image."""
    try:
        # Open the image
        image = Image.open(image_path).convert('RGBA')
        width, height = image.size
        
        # Create a transparent layer for the watermark
        txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw(draw=txt_layer)
        
        # Try to use a TrueType font; fallback to default if not available
        try:
            font = truetype("arial.ttf", font_size)
        except:
            font = truetype("DejaVuSans.ttf", font_size)
            
        # Calculate text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Determine position
        margin = 10
        if position == 'top-left':
            x, y = margin, margin
        elif position == 'top-center':
            x, y = (width - text_width) // 2, margin
        elif position == 'top-right':
            x, y = width - text_width - margin, margin
        elif position == 'center':
            x, y = (width - text_width) // 2, (height - text_height) // 2
        elif position == 'bottom-left':
            x, y = margin, height - text_height - margin
        elif position == 'bottom-center':
            x, y = (width - text_width) // 2, height - text_height - margin
        else:  # Default to bottom-right
            x, y = width - text_width - margin, height - text_height - margin
            
        # Draw the text
        draw.text((x, y), text, fill=color + (255,), font=font)
        
        # Composite the text layer onto the original image
        watermarked = Image.alpha_composite(image, txt_layer)
        
        # Convert back to RGB if saving as JPEG
        if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
            watermarked = watermarked.convert('RGB')
            
        # Save the watermarked image
        watermarked.save(output_path)
        print(f"Watermarked image saved to {output_path}")
    except Exception as e:
        print(f"Error adding watermark to {image_path}: {e}")

def process_image(image_path, font_size, color, position):
    """Process a single image file."""
    # Get EXIF data
    exif_data = get_exif_data(image_path)
    
    # Extract capture date
    capture_date = get_capture_date(exif_data)
    if not capture_date:
        print(f"No capture date found in EXIF data for {image_path}")
        return
    
    # Create watermark text
    watermark_text = capture_date
    
    # Determine output directory
    directory = os.path.dirname(image_path)
    filename = os.path.basename(image_path)
    name, ext = os.path.splitext(filename)
    
    output_dir = os.path.join(directory, f"{name}_watermark")
    os.makedirs(output_dir, exist_ok=True)
    
    # Define output path
    output_path = os.path.join(output_dir, filename)
    
    # Add watermark
    add_watermark(image_path, output_path, watermark_text, font_size, color, position)

def main():
    """Main function to parse arguments and process images."""
    parser = argparse.ArgumentParser(description="Add a text watermark with capture date to images.")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument("--font-size", type=int, default=20, help="Font size for the watermark (default: 20)")
    parser.add_argument("--color", nargs=3, type=int, default=[255, 255, 255], 
                        metavar=('R', 'G', 'B'), help="Watermark color as RGB values (default: 255 255 255)")
    parser.add_argument("--position", choices=[
        'top-left', 'top-center', 'top-right', 
        'center', 
        'bottom-left', 'bottom-center', 'bottom-right'
    ], default='bottom-right', help="Position of the watermark (default: bottom-right)")
    
    args = parser.parse_args()
    
    # Validate image path
    if not os.path.isfile(args.image_path):
        print(f"Error: File not found at {args.image_path}")
        return
    
    # Validate color values
    if any(c < 0 or c > 255 for c in args.color):
        print("Error: Color values must be between 0 and 255")
        return
    
    # Process the image
    process_image(args.image_path, args.font_size, tuple(args.color), args.position)

if __name__ == "__main__":
    main()