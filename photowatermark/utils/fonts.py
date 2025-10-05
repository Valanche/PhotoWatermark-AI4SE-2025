"""
Font utilities for the PhotoWatermark-AI4SE application.
"""
import matplotlib.font_manager as fm
from fontTools.ttLib import TTFont
import os


def get_system_fonts():
    """
    Get a list of system fonts with Chinese names when available.
    
    Returns:
        list: Sorted list of unique font names (Chinese names prioritized)
    """
    try:
        # Find all system font files
        font_files = fm.findSystemFonts()
        
        # Extract font names
        font_names = []
        for font_path in font_files:
            try:
                # First try to get font name with fontTools for better Chinese name support
                tt = TTFont(font_path)
                chinese_name = None
                
                # Look for Chinese name (Simplified Chinese, Windows platform)
                for record in tt['name'].names:
                    if (record.nameID == 4 and  # Full font name
                        record.platformID == 3 and  # Windows
                        record.langID == 0x0804):   # Simplified Chinese
                        chinese_name = record.toUnicode()
                        break
                
                # If no Chinese name found, fall back to English name
                if not chinese_name:
                    font_prop = fm.FontProperties(fname=font_path)
                    chinese_name = font_prop.get_name()
                
                font_names.append(chinese_name)
            except Exception:
                # Skip fonts that cause errors
                continue
        
        # Remove duplicates and sort
        unique_fonts = sorted(set(font_names))
        return unique_fonts
    except Exception as e:
        print(f"Error getting system fonts: {e}")
        # Return some default fonts if we can't get system fonts
        return ["Arial", "Times New Roman", "Courier New", "Verdana", "Helvetica"]


def get_font_path_by_name(font_name):
    """
    Get the file path for a given font name.
    
    Args:
        font_name (str): The name of the font
        
    Returns:
        str: Path to the font file, or None if not found
    """
    try:
        # Find all system font files
        font_files = fm.findSystemFonts()
        
        # Search for the font
        for font_path in font_files:
            try:
                # Get font name with fontTools
                tt = TTFont(font_path)
                chinese_name = None
                english_name = None
                
                # Look for Chinese name (Simplified Chinese, Windows platform)
                for record in tt['name'].names:
                    if record.nameID == 4 and record.platformID == 3 and record.langID == 0x0804:
                        chinese_name = record.toUnicode()
                    elif record.nameID == 4 and record.platformID == 3 and record.langID == 0x0409:
                        english_name = record.toUnicode()
                
                # Check if this is the font we're looking for
                if chinese_name == font_name or english_name == font_name:
                    return font_path
            except Exception:
                # Skip fonts that cause errors
                continue
                
        # If not found with fontTools, try with matplotlib
        for font_path in font_files:
            try:
                font_prop = fm.FontProperties(fname=font_path)
                if font_prop.get_name() == font_name:
                    return font_path
            except Exception:
                continue
                
        return None
    except Exception as e:
        print(f"Error finding font path: {e}")
        return None


def get_safe_font_list():
    """
    Get a list of commonly available fonts across different systems.
    
    Returns:
        list: List of safe font names
    """
    return [
        "Arial", "Times New Roman", "Courier New", "Verdana", "Helvetica",
        "Tahoma", "Trebuchet MS", "Georgia", "Palatino", "Garamond",
        "Comic Sans MS", "Impact", "Lucida Console", "Lucida Sans Unicode",
        "Microsoft Sans Serif", "Segoe UI", "Calibri", "Cambria", "Candara"
    ]


if __name__ == "__main__":
    # Test the font functions
    print("Testing font utilities...")
    
    # Get system fonts
    fonts = get_system_fonts()
    print(f"Found {len(fonts)} system fonts")
    print("First 10 fonts:", fonts[:10])
    
    # Get safe fonts
    safe_fonts = get_safe_font_list()
    print(f"Safe font list contains {len(safe_fonts)} fonts")
    print("Sample safe fonts:", safe_fonts[:5])
    
    # Test font path lookup
    if fonts:
        test_font = fonts[0]
        path = get_font_path_by_name(test_font)
        print(f"Path for '{test_font}': {path}")