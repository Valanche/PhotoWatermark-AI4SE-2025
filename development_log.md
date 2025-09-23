# PhotoWatermark-AI4SE Development Log

## Initial Implementation

User requested a command-line program in Python that would:
1. Accept an image file path as input
2. Read EXIF information to extract capture date (year-month-day) as watermark text
3. Allow customizable font size, color, and position (top-left, center, bottom-right, etc.)
4. Draw text watermark on images and save to a new directory named `<original_directory>_watermark`

I implemented the initial version with all requested features:
- Created `photowatermark.py` with full functionality
- Added `README.md` with usage instructions
- Added `requirements.txt` for dependencies (Pillow)
- Implemented EXIF data extraction and watermarking features

## First Issue: Directory Processing

User tried to run the program with a directory path but got an error:
```
Error: File not found at C:\Users\block\Desktop\awd
```

Analysis showed that the program only supported single files, not directories.

### Fix:
1. Modified the program to handle both single files and directories
2. Added support for processing all images in a directory
3. Updated README with directory processing examples

## Second Issue: ImageDraw Error

User encountered an error when running the program:
```
Error adding watermark to C:\Users\block\Desktop\awd\pexels-neuman-7208376.jpg: __init__() got an unexpected keyword argument 'draw'
```

Analysis showed incorrect usage of ImageDraw:
- Wrong import: `from PIL.ImageDraw import ImageDraw`
- Wrong instantiation: `draw = ImageDraw(draw=txt_layer)`

### Fix:
1. Corrected import to: `from PIL import ImageDraw`
2. Fixed instantiation to: `draw = ImageDraw.Draw(txt_layer)`

## Third Issue: Output Directory Structure

User noted that images were being saved in subdirectories of the original directory rather than a single `_watermark` directory.

Analysis confirmed that the program was creating separate subdirectories for each image.

### Fix:
1. Modified `process_directory` to create a single output directory named `{original_directory}_watermark`
2. Updated `process_image` to accept an optional `output_dir` parameter
3. Ensured all watermarked images are saved in the same directory when processing a directory

## Fourth Issue: EXIF Information Loss

User pointed out that watermarked images lost their original EXIF information.

Analysis confirmed that the save operation did not preserve EXIF data.

### Fix:
1. Modified `add_watermark` to extract and preserve EXIF data from original images
2. Updated save operation to include EXIF data in watermarked images
3. Ensured that all metadata is preserved in the watermarked versions

## Current Status

The program now:
1. Processes both single image files and entire directories
2. Correctly uses ImageDraw for watermarking
3. Saves all watermarked images in a single `_watermark` subdirectory
4. Preserves original EXIF information in watermarked images
5. Supports customizable font size, color, and position for watermarks
6. Extracts capture date from EXIF data for watermark text

## Git Commits

1. Initial implementation:
   ```
   feat: implement photo watermark CLI tool with EXIF date extraction
   ```

2. Directory processing enhancement:
   ```
   feat: enhance photo watermark tool to support directory processing
   ```

3. Output directory structure fix:
   ```
   fix: update image saving logic to use a single _watermark directory
   ```

4. EXIF preservation (pending commit):
   ```
   fix: preserve EXIF information in watermarked images
   ```

This concludes the development log for the PhotoWatermark tool.