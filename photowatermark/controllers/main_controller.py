"""
Main controller for the PhotoWatermark-AI4SE application.
This module handles the application logic and coordinates between the view and model.
"""
import threading
from tkinter import messagebox
from PIL import Image

from photowatermark.views.main_window import MainWindow
from photowatermark.models.image_processor import ImageProcessor
from photowatermark.utils.dialogs import show_error_message


class MainController:
    def __init__(self):
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
                    
                    # Process the image
                    image = self.image_processor.process_image_for_export(
                        image,
                        settings.get('format_rule', '原格式'),
                        settings.get('quality', 95)
                    )
                    
                    # Resize image if needed
                    image = self.image_processor.resize_image(
                        image,
                        settings.get('resize_option', '原图尺寸'),
                        settings.get('resize_value', ''),
                        settings.get('original_width'),
                        settings.get('original_height')
                    )
                    
                    # Save the processed image
                    _, ext = os.path.splitext(output_path)
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
        messagebox.showinfo("完成", f"导出完毕！成功导出 {success_count} 个文件。")
        
        # Call the custom callback if provided
        if self.export_callback:
            self.export_callback(success_count)