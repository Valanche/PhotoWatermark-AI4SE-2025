"""
Main controller for the PhotoWatermark-AI4SE application.
This module handles the application logic and coordinates between the view and model.
"""
import threading
import os
from tkinter import messagebox
from PIL import Image

from photowatermark.views.main_window import MainWindow
from photowatermark.models.image_processor import ImageProcessor
from photowatermark.utils.dialogs import show_error_message


class MainController:
    def __init__(self, view=None):
        if view is not None:
            self.main_window = view
        else:
            self.main_window = MainWindow()
        self.image_processor = ImageProcessor()
        self.export_callback = None

    def run(self):
        """Start the application"""
        self.main_window.root.mainloop()

    def set_export_callback(self, callback):
        """Set callback function to be called when export is completed"""
        self.export_callback = callback

    def export_images(self, image_paths, output_dir, settings):
        """
        Export images with the given settings
        Settings should be a dict containing export settings like naming rules, format, quality, etc.
        """
        # Run export in a separate thread to avoid blocking the UI
        export_thread = threading.Thread(
            target=self._perform_export,
            args=(image_paths, output_dir, settings),
            daemon=True
        )
        export_thread.start()

    def _perform_export(self, image_paths, output_dir, settings):
        """Perform the actual export operation in a background thread"""
        try:
            success_count = 0
            
            for img_path in image_paths:
                try:
                    # Generate output filename based on settings
                    output_path = self.image_processor.generate_output_filename(
                        img_path,
                        output_dir,
                        settings.get('naming_rule', '保留原名'),
                        settings.get('naming_value', ''),
                        settings.get('format_rule', '原格式')
                    )
                    
                    # Open the image first
                    image = Image.open(img_path)
                    
                    # Apply watermark if enabled
                    if settings.get('watermark_enabled', False):
                        watermark_settings = {
                            'text': settings.get('watermark_text', 'Sample Text'),
                            'transparency': settings.get('watermark_transparency', 50),
                            'position': settings.get('watermark_position', 'bottom-right'),
                            'font_size': settings.get('watermark_font_size', 30),
                            'font_name': settings.get('watermark_font_name', 'Arial'),
                            'bold': settings.get('watermark_bold', False),
                            'italic': settings.get('watermark_italic', False),
                            'color': settings.get('watermark_color', (255, 255, 255))
                        }
                        
                        # Add custom coordinates if in custom position mode
                        if (settings.get('watermark_position') == "custom" and 
                            'watermark_custom_x' in settings and 
                            'watermark_custom_y' in settings):
                            watermark_settings['custom_x'] = settings['watermark_custom_x']
                            watermark_settings['custom_y'] = settings['watermark_custom_y']
                        
                        # Apply watermark to the image
                        result = self.image_processor.add_watermark_to_image(image, watermark_settings)
                        # Handle the case where add_watermark_to_image returns a tuple
                        if isinstance(result, tuple):
                            image = result[0]  # First element is the watermarked image
                        else:
                            image = result
                    
                    # Resize image if needed first
                    # Get original dimensions from the image if not provided in settings
                    original_width, original_height = image.size
                    image = self.image_processor.resize_image(
                        image,
                        settings.get('resize_option', '原图尺寸'),
                        settings.get('resize_value', ''),
                        settings.get('original_width', original_width),
                        settings.get('original_height', original_height)
                    )
                    
                    # Process the image for export format (handles RGBA to RGB conversion for JPEG)
                    _, ext = os.path.splitext(output_path)
                    image = self.image_processor.process_image_for_export(
                        image,
                        ext,  # Use actual output extension
                        settings.get('quality', 95)
                    )
                    
                    # Save the processed image
                    ext = ext.lower()
                    
                    if ext in ['.jpg', '.jpeg']:
                        image.save(
                            output_path,
                            "JPEG",
                            quality=settings.get('quality', 95),
                            exif=image.info.get('exif', b'')
                        )
                    elif ext == '.png':
                        image.save(output_path, "PNG", exif=image.info.get('exif', b''))
                    else:
                        image.save(output_path, exif=image.info.get('exif', b''))
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"导出文件失败 {img_path}: {str(e)}")
            
            # Call the callback in the main thread
            self.main_window.root.after(
                0, 
                lambda: self._on_export_complete(success_count)
            )
            
        except Exception as e:
            error_msg = f"导出过程中发生错误: {str(e)}"
            self.main_window.root.after(
                0, 
                lambda: show_error_message(self.main_window.root, "错误", error_msg)
            )

    def _on_export_complete(self, success_count):
        """Called when export is completed"""
        # Since the controller doesn't have access to the UI here, we'll rely on the callback
        # to handle UI updates
        
        # Call the custom callback if provided
        if self.export_callback:
            self.export_callback(success_count)
        else:
            # Fallback - this should ideally be handled by the UI layer
            # Import messagebox here to avoid circular imports
            try:
                from tkinter import messagebox
                messagebox.showinfo("完成", f"导出完毕！成功导出 {success_count} 个文件。") 
            except:
                print(f"导出完毕！成功导出 {success_count} 个文件。")  # Fallback to console