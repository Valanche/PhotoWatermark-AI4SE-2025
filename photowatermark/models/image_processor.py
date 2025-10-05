"""
Image processing module for the PhotoWatermark-AI4SE application.
"""
from PIL import Image, ImageTk, ImageDraw
try:
    from PIL import ImageFont
except ImportError:
    ImageFont = None
import os
from typing import List
from photowatermark.utils.constants import THUMBNAIL_SIZE


class ImageProcessor:
    def __init__(self, thumbnail_size=None):
        self.thumbnail_size = thumbnail_size or THUMBNAIL_SIZE
        self.thumbnail_images = []  # Store references to prevent garbage collection

    def create_thumbnail(self, image_path):
        """为指定图片路径创建缩略图"""
        try:
            image = Image.open(image_path)
            image_copy = image.copy()  # 避免关闭原图
            # 兼容不同版本的PIL
            try:
                image_copy.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            except AttributeError:
                # 对于旧版本的PIL
                image_copy.thumbnail(self.thumbnail_size, Image.LANCZOS)
            return ImageTk.PhotoImage(image_copy)
        except Exception:
            # 如果无法创建缩略图，返回占位符
            placeholder = Image.new('RGB', self.thumbnail_size, (200, 200, 200))
            return ImageTk.PhotoImage(placeholder)

    def resize_image(self, image, resize_option, resize_value, original_width=None, original_height=None):
        """根据用户设置调整图片尺寸"""
        if resize_option == "原图尺寸" or not resize_value:
            return image
        else:
            try:
                value = int(resize_value) if resize_value else 100
                if not original_width or not original_height:
                    original_width, original_height = image.size
                
                if resize_option == "按比例缩放":
                    # 按百分比缩放
                    new_width = int(original_width * value / 100)
                    new_height = int(original_height * value / 100)
                elif resize_option == "指定宽度":
                    # 按指定宽度缩放，保持宽高比
                    new_width = value
                    new_height = int(original_height * value / original_width)
                elif resize_option == "指定高度":
                    # 按指定高度缩放，保持宽高比
                    new_height = value
                    new_width = int(original_width * value / original_height)
                else:
                    return image  # 默认返回原图
                
                # 兼容不同版本的Pillow
                try:
                    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                except AttributeError:
                    return image.resize((new_width, new_height), Image.LANCZOS)
            except ValueError:
                # 如果输入的值不是有效数字，返回原图
                return image

    def generate_output_filename(self, input_path, output_dir, naming_rule, naming_value, format_rule):
        """根据用户设置生成输出文件名"""
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        
        if naming_rule == "添加前缀":
            if naming_value:
                name = naming_value + name
        elif naming_rule == "添加后缀":
            if naming_value:
                name = name + naming_value
        # "保留原名"选项不需要更改
        
        # 根据输出格式决定扩展名
        if format_rule == "JPEG":
            ext = ".jpeg"
        elif format_rule == "PNG":
            ext = ".png"
        # "原格式"选项保持原扩展名
        
        output_path = os.path.join(output_dir, f"{name}{ext}")
        return output_path

    def process_image_for_export(self, image, output_format, quality=95):
        """处理图片以准备导出"""
        # 如果需要转换格式，确保图片模式正确
        if output_format.lower() in ['.jpg', '.jpeg'] and image.mode in ('RGBA', 'LA', 'P'):
            # JPEG不支持透明通道，转换为RGB
            if image.mode == 'P':
                image = image.convert("RGBA")
            image = image.convert("RGB")
        
        return image

    def add_watermark_to_image(self, image, watermark_settings):
        """为图片添加文本水印"""
        # Convert to RGBA if not already (to support transparency)
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        # Create a transparent layer for the watermark
        txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Get watermark settings
        text = watermark_settings.get('text', 'Sample Text')
        font_size = watermark_settings.get('font_size', 30)
        color = watermark_settings.get('color', (255, 255, 255))
        transparency = watermark_settings.get('transparency', 50)
        position = watermark_settings.get('position', 'bottom-right')
        font_name = watermark_settings.get('font_name', 'Arial')  # 默认字体
        
        # Calculate transparency value (0-255)
        alpha = int((transparency / 100) * 255)
        
        # Ensure alpha is within valid range
        alpha = max(0, min(255, alpha))
        
        # Create color with transparency
        rgba_color = (*color, alpha)
        
        # Handle font loading safely with font name support
        font = None
        if ImageFont:
            try:
                # Try to load the specified font by name with style support
                from photowatermark.utils.fonts import get_stylized_font_path
                font_path = get_stylized_font_path(font_name, bold=watermark_settings.get('bold', False), 
                                                  italic=watermark_settings.get('italic', False))
                if font_path and os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                else:
                    # Fallback to Arial if font not found
                    font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    # Try Arial as fallback
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    try:
                        # Try DejaVuSans as another fallback
                        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
                    except:
                        # Use default font if no TrueType fonts are available
                        font = ImageFont.load_default()
        else:
            # If ImageFont is not available, use default
            font = None
        
        # Calculate text size
        text_width = 0
        text_height = 0
        
        if font and ImageFont:
            try:
                # For Pillow >= 10.0.0
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except AttributeError:
                # For older versions of Pillow
                try:
                    text_width, text_height = draw.textsize(text, font=font)
                except:
                    # Fallback to a default size
                    text_width, text_height = font_size * len(text) // 2, font_size
        else:
            # If no font is available, estimate text size
            text_width, text_height = font_size * len(text) // 2, font_size
        
        # Determine position
        width, height = image.size
        margin = 10
        
        # Check if using custom coordinates
        if position == 'custom' and 'custom_x' in watermark_settings and 'custom_y' in watermark_settings:
            x = watermark_settings['custom_x']
            y = watermark_settings['custom_y']
            # Ensure the coordinates are within image bounds
            x = max(0, min(x, width - text_width))
            y = max(0, min(y, height - text_height))
        elif position == 'top-left':
            x, y = margin, margin
        elif position == 'top-center':
            x, y = (width - text_width) // 2, margin
        elif position == 'top-right':
            x, y = width - text_width - margin, margin
        elif position == 'middle-left':
            x, y = margin, (height - text_height) // 2
        elif position == 'center':
            x, y = (width - text_width) // 2, (height - text_height) // 2
        elif position == 'middle-right':
            x, y = width - text_width - margin, (height - text_height) // 2
        elif position == 'bottom-left':
            x, y = margin, height - text_height - margin
        elif position == 'bottom-center':
            x, y = (width - text_width) // 2, height - text_height - margin
        else:  # Default to bottom-right
            x, y = width - text_width - margin, height - text_height - margin
        
        # Draw the text
        draw.text((x, y), text, fill=rgba_color, font=font)
        
        # Composite the text layer onto the original image
        watermarked = Image.alpha_composite(image, txt_layer)
        
        return watermarked