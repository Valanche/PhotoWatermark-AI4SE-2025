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


def _get_font_info(font_path):
    """
    Get font information from font file.
    
    Args:
        font_path (str): Path to the font file
        
    Returns:
        dict: Font information including family, subfamily, and style flags
    """
    try:
        tt = TTFont(font_path)
        name_table = tt['name']
        
        # Get font information
        font_family = None
        font_subfamily = None
        full_name = None
        
        # Prefer English (US) names
        for record in name_table.names:
            if record.nameID == 1 and record.platformID == 3 and record.langID == 0x0409:  # Font Family
                font_family = record.toUnicode()
            elif record.nameID == 2 and record.platformID == 3 and record.langID == 0x0409:  # Font Subfamily
                font_subfamily = record.toUnicode()
            elif record.nameID == 4 and record.platformID == 3 and record.langID == 0x0409:  # Full Font Name
                full_name = record.toUnicode()
                
        # Fallback to any available names if English not found
        if not font_family or not font_subfamily or not full_name:
            for record in name_table.names:
                if record.nameID == 1 and not font_family:
                    font_family = record.toUnicode()
                elif record.nameID == 2 and not font_subfamily:
                    font_subfamily = record.toUnicode()
                elif record.nameID == 4 and not full_name:
                    full_name = record.toUnicode()
        
        return {
            'family': font_family,
            'subfamily': font_subfamily,
            'full_name': full_name,
            'path': font_path,
            'is_bold': font_subfamily and ('bold' in font_subfamily.lower() or 'heavy' in font_subfamily.lower()),
            'is_italic': font_subfamily and ('italic' in font_subfamily.lower() or 'oblique' in font_subfamily.lower())
        }
    except Exception:
        return None


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


def get_stylized_font_path(base_font_name, bold=False, italic=False):
    """
    Get the file path for a stylized version of a font (bold, italic, or both)
    by matching font family and subfamily information.
    
    Args:
        base_font_name (str): The base font name
        bold (bool): Whether to find bold version
        italic (bool): Whether to find italic version
        
    Returns:
        str: Path to the stylized font file, or base font if not found
    """
    try:
        # Find all system font files
        font_files = fm.findSystemFonts()
        
        # First find the base font info
        base_info = None
        for font_path in font_files:
            info = _get_font_info(font_path)
            if info and (info['full_name'] == base_font_name):
                base_info = info
                break
                
        if not base_info or not base_info['family']:
            # If we can't find base font info, return base font path
            return get_font_path_by_name(base_font_name)
            
        # Now look for a matching font with the requested styles
        best_match = None
        for font_path in font_files:
            info = _get_font_info(font_path)
            if not info or info['family'] != base_info['family']:
                continue
                
            # Check if this font matches the requested styles exactly
            matches_bold = info['is_bold'] == bold
            matches_italic = info['is_italic'] == italic
            
            if matches_bold and matches_italic:
                return font_path
                
            # Keep track of any match for fallback
            if best_match is None:
                matches_bold_loose = (not bold) or info['is_bold']
                matches_italic_loose = (not italic) or info['is_italic']
                if matches_bold_loose and matches_italic_loose:
                    best_match = font_path
                
        # If no exact match found, return best match or base font
        return best_match if best_match else base_info['path']
    except Exception as e:
        print(f"Error finding stylized font path: {e}")
        return get_font_path_by_name(base_font_name)


def font_supports_style(font_name, bold=False, italic=False):
    """
    Check if a font supports specific styles (bold, italic).
    
    Args:
        font_name (str): The font name
        bold (bool): Check for bold support
        italic (bool): Check for italic support
        
    Returns:
        bool: True if font supports the requested styles, False otherwise
    """
    try:
        stylized_path = get_stylized_font_path(font_name, bold=bold, italic=italic)
        base_path = get_font_path_by_name(font_name)
        
        # If we got a different path than the base font, it supports the style
        return stylized_path and base_path and stylized_path != base_path
    except Exception:
        return False


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
        test_font = "Arial"
        path = get_font_path_by_name(test_font)
        print(f"Path for '{test_font}': {path}")
        
        # Test stylized font lookup
        stylized_path = get_stylized_font_path(test_font, bold=True)
        print(f"Bold version path for '{test_font}': {stylized_path}")
        
        stylized_path = get_stylized_font_path(test_font, italic=True)
        print(f"Italic version path for '{test_font}': {stylized_path}")
        
        stylized_path = get_stylized_font_path(test_font, bold=True, italic=True)
        print(f"Bold+Italic version path for '{test_font}': {stylized_path}")


def font_supports_style(font_name, bold=False, italic=False):
    """
    Check if a font supports specific styles (bold, italic).
    
    Args:
        font_name (str): The font name
        bold (bool): Check for bold support
        italic (bool): Check for italic support
        
    Returns:
        bool: True if font supports the requested styles, False otherwise
    """
    try:
        stylized_path = get_stylized_font_path(font_name, bold=bold, italic=italic)
        base_path = get_font_path_by_name(font_name)
        
        # If we got a different path than the base font, it supports the style
        return stylized_path and base_path and stylized_path != base_path
    except Exception:
        return False