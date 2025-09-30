"""
Main window view for the PhotoWatermark-AI4SE application.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
from typing import List

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("警告: 未安装tkinterdnd2库，拖拽功能将不可用。请运行 'pip install tkinterdnd2' 来启用此功能。")

from photowatermark.views.widgets.thumbnail_list import ThumbnailList
from photowatermark.utils.dialogs import show_error_message


class MainWindow:
    def __init__(self):
        # 根据是否有DnD支持来创建适当的根窗口
        if HAS_DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
        
        self.root.title("PhotoWatermark-AI4SE - 迭代二")
        self.root.geometry("1200x800")
        
        # 存储导入的图片路径
        self.image_paths = []
        self.current_image_index = 0
        self.current_image = None
        
        # Initialize UI components
        self.thumbnail_list = None
        self.preview_canvas = None
        self.current_image = None
        
        # Export settings variables
        self.naming_var = None
        self.naming_entry = None
        self.quality_var = None
        self.quality_value_label = None
        self.format_var = None
        self.resize_var = None
        self.resize_entry = None
        self.resize_unit_label = None
        
        # Watermark settings variables
        self.watermark_enabled_var = None
        self.watermark_text_var = None
        self.watermark_text_entry = None
        self.watermark_transparency_var = None
        self.watermark_transparency_label = None
        self.watermark_position_var = None
        
        # Controller reference (will be set from main.py)
        self.controller = None
        
        self.setup_ui()
        
        # 设置拖拽事件（如果支持）
        if HAS_DND:
            self.setup_drag_drop()

    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部工具栏
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 导入按钮
        import_file_btn = ttk.Button(toolbar_frame, text="导入图片", command=self.import_images)
        import_file_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        import_folder_btn = ttk.Button(toolbar_frame, text="导入文件夹", command=self.import_folder)
        import_folder_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 文件列表区域
        list_frame = ttk.LabelFrame(main_frame, text="图片列表", width=200)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Create thumbnail list widget
        self.thumbnail_list = ThumbnailList(list_frame, on_select_callback=self.on_thumbnail_selected)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览")
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas用于显示预览图
        self.preview_canvas = tk.Canvas(preview_frame, bg='gray')
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 底部导出设置和按钮
        export_frame = ttk.LabelFrame(main_frame, text="导出设置")
        export_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 命名规则设置
        naming_frame = ttk.Frame(export_frame)
        naming_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(naming_frame, text="文件命名:").pack(side=tk.LEFT)
        self.naming_var = tk.StringVar(value="保留原名")
        naming_options = ["保留原名", "添加前缀", "添加后缀"]
        naming_combo = ttk.Combobox(naming_frame, textvariable=self.naming_var, values=naming_options, state="readonly", width=15)
        naming_combo.pack(side=tk.LEFT, padx=(5, 0))
        naming_combo.bind('<<ComboboxSelected>>', self.on_naming_change)
        
        self.naming_entry = ttk.Entry(naming_frame, width=15)
        self.naming_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.naming_entry.config(state='disabled')
        
        # JPEG质量设置（仅对JPEG输出）
        quality_frame = ttk.Frame(export_frame)
        quality_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.quality_var = tk.IntVar(value=95)
        quality_label = ttk.Label(quality_frame, text="JPEG质量:")
        quality_label.pack(side=tk.LEFT)
        quality_scale = ttk.Scale(quality_frame, from_=1, to=100, variable=self.quality_var, orient=tk.HORIZONTAL)
        quality_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        self.quality_value_label = ttk.Label(quality_frame, text=f"{self.quality_var.get()}")
        self.quality_var.trace_add("write", self.update_quality_label)
        self.quality_value_label.pack(side=tk.LEFT)
        
        # 输出格式设置
        format_frame = ttk.Frame(export_frame)
        format_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(format_frame, text="输出格式:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="原格式")
        format_options = ["原格式", "JPEG", "PNG"]
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, values=format_options, state="readonly", width=15)
        format_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 图片尺寸设置
        resize_frame = ttk.Frame(export_frame)
        resize_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(resize_frame, text="图片尺寸:").pack(side=tk.LEFT)
        self.resize_var = tk.StringVar(value="原图尺寸")
        resize_options = ["原图尺寸", "按比例缩放", "指定宽度", "指定高度"]
        resize_combo = ttk.Combobox(resize_frame, textvariable=self.resize_var, values=resize_options, state="readonly", width=15)
        resize_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        self.resize_entry = ttk.Entry(resize_frame, width=10)
        self.resize_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.resize_entry.config(state='disabled')
        
        # 动态标签（显示"%"或"px"）
        self.resize_unit_label = ttk.Label(resize_frame, text="%")
        self.resize_unit_label.pack(side=tk.LEFT)
        
        # 绑定尺寸选项改变事件
        resize_combo.bind('<<ComboboxSelected>>', self.on_resize_change)
        
        # 导出按钮
        export_btn = ttk.Button(export_frame, text="导出图片", command=self.export_images)
        export_btn.pack(pady=5)
        
        # 水印设置区域
        watermark_frame = ttk.LabelFrame(main_frame, text="水印设置")
        watermark_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 水印启用复选框
        self.watermark_enabled_var = tk.BooleanVar(value=False)
        watermark_enabled_check = ttk.Checkbutton(
            watermark_frame, 
            text="启用文本水印", 
            variable=self.watermark_enabled_var,
            command=self.on_watermark_enabled_change
        )
        watermark_enabled_check.pack(fill=tk.X, padx=5, pady=5)
        
        # 水印文字设置
        text_frame = ttk.Frame(watermark_frame)
        text_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(text_frame, text="水印文字:").pack(side=tk.LEFT)
        self.watermark_text_var = tk.StringVar(value="Sample Text")
        self.watermark_text_entry = ttk.Entry(text_frame, textvariable=self.watermark_text_var)
        self.watermark_text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 水印透明度设置
        transparency_frame = ttk.Frame(watermark_frame)
        transparency_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.watermark_transparency_var = tk.IntVar(value=50)
        transparency_label = ttk.Label(transparency_frame, text="水印透明度:")
        transparency_label.pack(side=tk.LEFT)
        transparency_scale = ttk.Scale(
            transparency_frame, 
            from_=0, 
            to=100, 
            variable=self.watermark_transparency_var, 
            orient=tk.HORIZONTAL
        )
        transparency_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        self.watermark_transparency_label = ttk.Label(transparency_frame, text=f"{self.watermark_transparency_var.get()}")
        self.watermark_transparency_var.trace_add("write", self.update_watermark_transparency_label)
        self.watermark_transparency_label.pack(side=tk.LEFT)
        
        # 水印位置设置
        position_frame = ttk.Frame(watermark_frame)
        position_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(position_frame, text="水印位置:").pack(side=tk.LEFT)
        self.watermark_position_var = tk.StringVar(value="bottom-right")
        position_options = [
            "top-left", "top-center", "top-right",
            "center", "bottom-left", "bottom-center", "bottom-right"
        ]
        position_combo = ttk.Combobox(
            position_frame, 
            textvariable=self.watermark_position_var, 
            values=position_options, 
            state="readonly", 
            width=15
        )
        position_combo.pack(side=tk.LEFT, padx=(5, 0))

    def setup_drag_drop(self):
        """设置拖拽功能"""
        # 为预览画布设置拖拽事件
        self.preview_canvas.drop_target_register(DND_FILES)
        self.preview_canvas.dnd_bind('<<Drop>>', self.on_drop)
        
        # 为缩略图画布设置拖拽事件
        self.thumbnail_list.canvas.drop_target_register(DND_FILES)
        self.thumbnail_list.canvas.dnd_bind('<<Drop>>', self.on_drop)
        
        # 为缩略图框架设置拖拽事件
        self.thumbnail_list.frame.drop_target_register(DND_FILES)
        self.thumbnail_list.frame.dnd_bind('<<Drop>>', self.on_drop)

    def on_naming_change(self, event=None):
        """当命名规则改变时"""
        if self.naming_var.get() in ["添加前缀", "添加后缀"]:
            self.naming_entry.config(state='enabled')
        else:
            self.naming_entry.config(state='disabled')
            self.naming_entry.delete(0, tk.END)

    def update_quality_label(self, *args):
        """更新质量标签"""
        self.quality_value_label.config(text=f"{self.quality_var.get()}")
    
    def on_watermark_enabled_change(self):
        """当水印启用状态改变时"""
        enabled = self.watermark_enabled_var.get()
        state = 'normal' if enabled else 'disabled'
        
        self.watermark_text_entry.config(state=state)
        # For the transparency scale, we need to enable/disable each widget differently
        # Scale widgets can't be disabled directly, so we'll just leave them enabled for now
        # but they won't matter if the watermark is not enabled during export
    
    def update_watermark_transparency_label(self, *args):
        """更新水印透明度标签"""
        self.watermark_transparency_label.config(text=f"{self.watermark_transparency_var.get()}")

    def on_resize_change(self, event=None):
        """当尺寸调整方式改变时"""
        if self.resize_var.get() in ["按比例缩放", "指定宽度", "指定高度"]:
            self.resize_entry.config(state='enabled')
            
            # 根据选择更新单位标签
            if self.resize_var.get() == "按比例缩放":
                self.resize_unit_label.config(text="%")
            elif self.resize_var.get() == "指定宽度":
                self.resize_unit_label.config(text="px")
            elif self.resize_var.get() == "指定高度":
                self.resize_unit_label.config(text="px")
        else:
            self.resize_entry.config(state='disabled')
            self.resize_entry.delete(0, tk.END)
            self.resize_unit_label.config(text="%")

    def on_thumbnail_selected(self, index):
        """当缩略图被选中时的回调"""
        self.current_image_index = index
        self.display_preview()

    def display_preview(self):
        """在预览区域显示当前图片"""
        if not self.image_paths or self.current_image_index >= len(self.image_paths):
            return
        
        try:
            image_path = self.image_paths[self.current_image_index]
            image = Image.open(image_path)
            
            # 获取预览画布的当前尺寸
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            # 如果画布尺寸不可用，则设置默认尺寸
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 600
                canvas_height = 400
                self.preview_canvas.config(width=canvas_width, height=canvas_height)
            
            # 保持宽高比缩放
            img_width, img_height = image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # 兼容不同版本的Pillow
            try:
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            except AttributeError:
                # 对于旧版本的Pillow
                image = image.resize((new_width, new_height), Image.LANCZOS)
            
            # 将图片转换为tkinter可以显示的格式
            self.current_image = ImageTk.PhotoImage(image)
            
            # 清除画布并显示新图片
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                canvas_width // 2, 
                canvas_height // 2, 
                anchor=tk.CENTER, 
                image=self.current_image
            )
            
            # 绑定窗口大小变化事件，以便动态调整预览图
            self.preview_canvas.bind("<Configure>", self.on_preview_resize)
            
        except Exception as e:
            error_msg = f"无法加载图片 {image_path}: {str(e)}"
            show_error_message(self.root, "错误", error_msg)
    
    def on_preview_resize(self, event):
        """当预览画布大小改变时重新调整预览图"""
        # 只有在有图片的情况下才重新绘制
        if self.image_paths and 0 <= self.current_image_index < len(self.image_paths):
            # 使用after来防止频繁重绘，提高性能
            if hasattr(self, '_resize_job'):
                self.root.after_cancel(self._resize_job)
            self._resize_job = self.root.after(100, self.display_preview)

    def import_images(self):
        """导入图片文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("BMP", "*.bmp"),
                ("TIFF", "*.tiff *.tif"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_paths:
            self.add_images(file_paths)

    def import_folder(self):
        """导入文件夹中的图片"""
        folder_path = filedialog.askdirectory(title="选择图片文件夹")
        
        if folder_path:
            # 获取文件夹中所有支持的图片文件
            supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
            image_paths = []

            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(supported_extensions):
                        image_paths.append(os.path.join(root, file))

            if image_paths:
                self.add_images(image_paths)
            else:
                messagebox.showinfo("提示", "所选文件夹中没有找到支持的图片格式文件。")

    def add_images(self, file_paths: List[str]):
        """添加图片到列表"""
        new_paths = [path for path in file_paths if path not in self.image_paths]

        if not new_paths:
            messagebox.showinfo("提示", "所有选择的文件都已存在列表中。")
            return

        for path in new_paths:
            self.image_paths.append(path)
            # Add to thumbnail list
            self.thumbnail_list.add_thumbnail(path)

        # 如果这是第一次添加图片，自动选择第一张
        if len(self.image_paths) == len(new_paths):
            self.current_image_index = 0
            self.thumbnail_list.select_item(0)
            self.display_preview()

    def export_images(self):
        """导出图片"""
        if not self.image_paths:
            messagebox.showwarning("警告", "没有要导出的图片。")
            return
        
        output_dir = filedialog.askdirectory(title="选择导出目录")
        if not output_dir:
            return  # 用户取消了操作
        
        # 确保输出目录不是输入图片的目录（完全禁止）
        input_dir = os.path.dirname(self.image_paths[0]) if self.image_paths else ""
        if input_dir:
            try:
                if os.path.samefile(output_dir, input_dir):
                    messagebox.showerror("错误", "禁止导出到原文件夹，以防止覆盖原图！请选择其他目录。")
                    return
            except OSError:
                # 如果路径在不同驱动器上，使用字符串比较
                if os.path.normpath(output_dir) == os.path.normpath(input_dir):
                    messagebox.showerror("错误", "禁止导出到原文件夹，以防止覆盖原图！请选择其他目录。")
                    return
        
        # Prepare settings dict
        settings = {
            'naming_rule': self.naming_var.get(),
            'naming_value': self.naming_entry.get().strip(),
            'format_rule': self.format_var.get(),
            'quality': self.quality_var.get(),
            'resize_option': self.resize_var.get(),
            'resize_value': self.resize_entry.get(),
            
            # Watermark settings
            'watermark_enabled': self.watermark_enabled_var.get(),
            'watermark_text': self.watermark_text_var.get(),
            'watermark_transparency': self.watermark_transparency_var.get(),
            'watermark_position': self.watermark_position_var.get(),
            'watermark_font_size': 30,  # Default font size
            'watermark_color': (255, 255, 255)  # Default white color
        }
        
        # If controller is available, use it; otherwise use direct approach
        if self.controller:
            self.controller.set_export_callback(self._on_export_complete)
            self.controller.export_images(self.image_paths, output_dir, settings)
        else:
            # Fallback to direct export (for standalone testing)
            import threading
            threading.Thread(target=self._export_process, args=(output_dir, settings), daemon=True).start()
    
    def _export_process(self, output_dir, settings=None):
        """在后台线程中执行导出操作"""
        if settings is None:
            # Fallback to current UI values if settings not provided
            settings = {
                'naming_rule': self.naming_var.get(),
                'naming_value': self.naming_entry.get().strip(),
                'format_rule': self.format_var.get(),
                'quality': self.quality_var.get(),
                'resize_option': self.resize_var.get(),
                'resize_value': self.resize_entry.get(),
                
                # Watermark settings
                'watermark_enabled': self.watermark_enabled_var.get(),
                'watermark_text': self.watermark_text_var.get(),
                'watermark_transparency': self.watermark_transparency_var.get(),
                'watermark_position': self.watermark_position_var.get(),
                'watermark_font_size': 30,  # Default font size
                'watermark_color': (255, 255, 255)  # Default white color
            }
        
        try:
            success_count = 0
            for i, img_path in enumerate(self.image_paths):
                try:
                    # 生成输出文件名
                    from photowatermark.models.image_processor import ImageProcessor
                    processor = ImageProcessor()
                    output_path = processor.generate_output_filename(
                        img_path, 
                        output_dir,
                        settings.get('naming_rule'),
                        settings.get('naming_value'),
                        settings.get('format_rule')
                    )
                    
                    # 打开图片
                    image = Image.open(img_path)
                    
                    # 根据设置调整图片尺寸
                    image = processor.resize_image(
                        image, 
                        settings.get('resize_option'), 
                        settings.get('resize_value'),
                        image.size[0],  # original width
                        image.size[1]   # original height
                    )
                    
                    # Apply watermark if enabled
                    if settings.get('watermark_enabled', False):
                        # Prepare watermark settings
                        watermark_settings = {
                            'text': settings.get('watermark_text', 'Sample Text'),
                            'transparency': settings.get('watermark_transparency', 50),
                            'position': settings.get('watermark_position', 'bottom-right'),
                            'font_size': settings.get('watermark_font_size', 30),
                            'color': settings.get('watermark_color', (255, 255, 255))
                        }
                        
                        # Apply watermark to the image
                        image = processor.add_watermark_to_image(image, watermark_settings)
                    
                    # 处理图片以准备导出
                    image = processor.process_image_for_export(
                        image, 
                        os.path.splitext(output_path)[1], 
                        settings.get('quality', 95)
                    )
                    
                    # 保存图片
                    _, ext = os.path.splitext(output_path)
                    ext = ext.lower()
                    
                    if ext in ['.jpg', '.jpeg']:
                        # 对于JPEG格式，使用用户设置的质量
                        image.save(output_path, "JPEG", quality=settings.get('quality', 95), exif=image.info.get('exif', b''))
                    elif ext == '.png':
                        # 对于PNG格式，保存时保留透明通道
                        image.save(output_path, "PNG", exif=image.info.get('exif', b''))
                    else:
                        # 对于其他格式，按原样保存
                        image.save(output_path, exif=image.info.get('exif', b''))
                    
                    success_count += 1
                except Exception as e:
                    print(f"导出文件失败 {img_path}: {str(e)}")
            
            # 在主线程中显示完成消息
            self.root.after(0, lambda: messagebox.showinfo("完成", f"导出完毕！成功导出 {success_count} 个文件。"))

        except Exception as e:
            error_msg = f"导出过程中发生错误: {str(e)}"
            self.root.after(0, lambda: show_error_message(self.root, "错误", error_msg))
    
    def _on_export_complete(self, success_count):
        """Callback when export is completed"""
        messagebox.showinfo("完成", f"导出完毕！成功导出 {success_count} 个文件。")
    
    def on_drop(self, event):
        """处理文件拖拽事件"""
        # 获取拖拽的文件路径
        if event.data:
            # 拖拽的数据通常是用花括号包围的路径，需要处理
            files = self.root.tk.splitlist(event.data)
            file_paths = []
            
            for file in files:
                # 清理路径字符串，移除可能的花括号
                clean_path = file.strip('{}')
                if os.path.isfile(clean_path):
                    # 检查文件扩展名是否为支持的图片格式
                    supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
                    if clean_path.lower().endswith(supported_extensions):
                        file_paths.append(clean_path)
                elif os.path.isdir(clean_path):
                    # 如果是文件夹，获取其中的所有图片
                    supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
                    for root, dirs, filenames in os.walk(clean_path):
                        for filename in filenames:
                            if filename.lower().endswith(supported_extensions):
                                file_paths.append(os.path.join(root, filename))
    
            if file_paths:
                self.add_images(file_paths)
            else:
                messagebox.showinfo("提示", "拖拽的文件中没有找到支持的图片格式。")

    def _export_process(self, output_dir):
        """在后台线程中执行导出操作"""
        try:
            success_count = 0
            for i, img_path in enumerate(self.image_paths):
                try:
                    # 生成输出文件名
                    from photowatermark.models.image_processor import ImageProcessor
                    processor = ImageProcessor()
                    output_path = processor.generate_output_filename(
                        img_path, 
                        output_dir,
                        self.naming_var.get(),
                        self.naming_entry.get().strip(),
                        self.format_var.get()
                    )
                    
                    # 打开图片
                    image = Image.open(img_path)
                    
                    # 根据设置调整图片尺寸
                    image = processor.resize_image(
                        image, 
                        self.resize_var.get(), 
                        self.resize_entry.get()
                    )
                    
                    # 处理图片以准备导出
                    image = processor.process_image_for_export(
                        image, 
                        os.path.splitext(output_path)[1], 
                        self.quality_var.get()
                    )
                    
                    # Apply watermark if enabled
                    if self.watermark_enabled_var.get():
                        # Prepare watermark settings
                        watermark_settings = {
                            'text': self.watermark_text_var.get(),
                            'transparency': self.watermark_transparency_var.get(),
                            'position': self.watermark_position_var.get(),
                            'font_size': 30,  # Default font size
                            'color': (255, 255, 255)  # Default white color
                        }
                        
                        # Apply watermark to the image
                        from photowatermark.models.image_processor import ImageProcessor
                        processor = ImageProcessor()
                        image = processor.add_watermark_to_image(image, watermark_settings)
                    
                    # 保存图片
                    _, ext = os.path.splitext(output_path)
                    ext = ext.lower()
                    
                    if ext in ['.jpg', '.jpeg']:
                        # 对于JPEG格式，使用用户设置的质量
                        image.save(output_path, "JPEG", quality=self.quality_var.get(), exif=image.info.get('exif', b''))
                    elif ext == '.png':
                        # 对于PNG格式，保存时保留透明通道
                        image.save(output_path, "PNG", exif=image.info.get('exif', b''))
                    else:
                        # 对于其他格式，按原样保存
                        image.save(output_path, exif=image.info.get('exif', b''))
                    
                    success_count += 1
                except Exception as e:
                    print(f"导出文件失败 {img_path}: {str(e)}")
            
            # 在主线程中显示完成消息
            self.root.after(0, lambda: messagebox.showinfo("完成", f"导出完毕！成功导出 {success_count} 个文件。"))
        except Exception as e:
            error_msg = f"导出过程中发生错误: {str(e)}"
            self.root.after(0, lambda: show_error_message(self.root, "错误", error_msg))