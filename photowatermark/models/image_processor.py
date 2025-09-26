"""
Image processing module for the PhotoWatermark-AI4SE application.
"""
from PIL import Image, ImageTk
import os
from typing import List


class ImageProcessor:
    def __init__(self, thumbnail_size=(80, 80)):
        self.thumbnail_size = thumbnail_size
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