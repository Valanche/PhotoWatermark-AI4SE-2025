"""
Main window view for the PhotoWatermark-AI4SE application.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import json
from typing import List

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("警告: 未安装tkinterdnd2库，拖拽功能将不可用。请运行 'pip install tkinterdnd2' 来启用此功能。")

from photowatermark.views.widgets.thumbnail_list import ThumbnailList
from photowatermark.utils.dialogs import show_error_message
from photowatermark.utils.constants import *


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
        self.watermark_font_size_var = None
        self.watermark_font_var = None  # 字体选择变量
        self.watermark_color = None  # RGB tuple for color
        
        # Custom position variables for drag-and-drop
        self.custom_watermark_x = None
        self.custom_watermark_y = None
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.watermark_start_x = 0
        self.watermark_start_y = 0
        
        # Configuration management variables
        self.config_name_var = None
        self.configs_dir = os.path.join(os.path.expanduser("~"), ".photowatermark", "configs")
        
        # Application state variables
        self.app_state_file = os.path.join(os.path.expanduser("~"), ".photowatermark", "app_state.json")
        
        # Controller reference (will be set from main.py)
        self.controller = None
        
        self.setup_ui()
        
        # 确保配置目录存在
        os.makedirs(self.configs_dir, exist_ok=True)
        
        # 加载上次的应用程序状态
        self.load_app_state()
        
        # 设置拖拽事件（如果支持）
        if HAS_DND:
            self.setup_drag_drop()
        
        # 绑定窗口关闭事件以保存状态
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        
        # 导出按钮框架
        export_btn_frame = ttk.Frame(export_frame)
        export_btn_frame.pack(pady=5)
        
        # 导出当前图片按钮
        export_current_btn = ttk.Button(export_btn_frame, text="导出当前图片", command=self.export_current_image)
        export_current_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 导出所有图片按钮
        export_btn = ttk.Button(export_btn_frame, text="导出图片", command=self.export_images)
        export_btn.pack(side=tk.LEFT)
        
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
        # 绑定文本变化事件以实时更新预览
        self.watermark_text_var.trace_add("write", self.update_preview_delayed)
        
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
        # 绑定透明度变化事件以实时更新预览
        self.watermark_transparency_var.trace_add("write", self.update_preview_delayed)
        
        # 水印位置设置
        position_frame = ttk.Frame(watermark_frame)
        position_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(position_frame, text="水印位置:").pack(side=tk.LEFT)
        self.watermark_position_var = tk.StringVar(value="bottom-right")
        position_options = [
            "top-left", "top-center", "top-right",
            "middle-left", "center", "middle-right",
            "bottom-left", "bottom-center", "bottom-right"
        ]
        position_combo = ttk.Combobox(
            position_frame, 
            textvariable=self.watermark_position_var, 
            values=position_options, 
            state="readonly", 
            width=15
        )
        position_combo.pack(side=tk.LEFT, padx=(5, 0))
        # 绑定位置变化事件以实时更新预览
        position_combo.bind('<<ComboboxSelected>>', self.on_watermark_position_change)
        
        # 水印字体大小设置
        font_size_frame = ttk.Frame(watermark_frame)
        font_size_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(font_size_frame, text="字体大小:").pack(side=tk.LEFT)
        self.watermark_font_size_var = tk.IntVar(value=30)
        font_size_scale = ttk.Scale(
            font_size_frame,
            from_=10,
            to=100,
            variable=self.watermark_font_size_var,
            orient=tk.HORIZONTAL
        )
        font_size_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        self.watermark_font_size_label = ttk.Label(font_size_frame, text=f"{self.watermark_font_size_var.get()}")
        self.watermark_font_size_var.trace_add("write", self.update_watermark_font_size_label)
        self.watermark_font_size_label.pack(side=tk.LEFT)
        # 绑定字体大小变化事件以实时更新预览
        self.watermark_font_size_var.trace_add("write", self.update_preview_delayed)
        
        # 水印字体选择设置
        font_selection_frame = ttk.Frame(watermark_frame)
        font_selection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(font_selection_frame, text="字体选择:").pack(side=tk.LEFT)
        self.watermark_font_var = tk.StringVar(value="Arial")  # 默认字体
        # 获取系统字体列表
        try:
            from photowatermark.utils.fonts import get_system_fonts
            font_list = get_system_fonts()
        except:
            # 如果获取失败，使用安全字体列表
            from photowatermark.utils.fonts import get_safe_font_list
            font_list = get_safe_font_list()
        
        # 创建字体选择下拉框
        font_combo = ttk.Combobox(
            font_selection_frame,
            textvariable=self.watermark_font_var,
            values=font_list,
            state="readonly",
            width=15
        )
        font_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        # 绑定字体变化事件以实时更新预览
        font_combo.bind('<<ComboboxSelected>>', self.on_watermark_font_change)
        
        # 配置管理框架
        config_frame = ttk.LabelFrame(watermark_frame, text="配置管理", padding=(5, 5))
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 保存和加载配置按钮
        save_config_btn = ttk.Button(config_frame, text="保存配置", command=self.save_config)
        save_config_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        load_config_btn = ttk.Button(config_frame, text="加载配置", command=self.load_config)
        load_config_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 删除配置按钮
        delete_config_btn = ttk.Button(config_frame, text="删除配置", command=self.delete_config)
        delete_config_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 配置名称输入
        ttk.Label(config_frame, text="配置名称:").pack(side=tk.LEFT, padx=(10, 5))
        self.config_name_var = tk.StringVar(value="默认配置")
        config_name_entry = ttk.Entry(config_frame, textvariable=self.config_name_var, width=15)
        config_name_entry.pack(side=tk.LEFT)

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
        
        # Update preview when watermark is enabled/disabled
        self.display_preview()
    
    def update_watermark_transparency_label(self, *args):
        """更新水印透明度标签"""
        self.watermark_transparency_label.config(text=f"{self.watermark_transparency_var.get()}")
    
    def update_watermark_font_size_label(self, *args):
        """更新水印字体大小标签"""
        self.watermark_font_size_label.config(text=f"{self.watermark_font_size_var.get()}")
    
    def on_watermark_position_change(self, event):
        """当水印位置改变时更新预览"""
        self.update_preview_delayed()
    
    def on_watermark_font_change(self, event):
        """当水印字体改变时更新预览"""
        self.update_preview_delayed()
    
    def update_preview_delayed(self, *args):
        """延迟更新预览以避免频繁更新"""
        # 取消之前的更新请求（如果有的话）
        if hasattr(self, '_preview_update_job'):
            self.root.after_cancel(self._preview_update_job)
        
        # 设置新的更新请求，延迟100毫秒执行
        self._preview_update_job = self.root.after(100, self.display_preview)
    
    def on_watermark_canvas_click(self, event):
        """处理水印画布点击事件"""
        if not self.watermark_enabled_var.get():
            return
        
        # Convert the click coordinates to image coordinates 
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 600
            canvas_height = 400
        
        # Get the currently displayed image (could be original or with watermark)
        image_path = self.image_paths[self.current_image_index]
        original_image = Image.open(image_path)
        
        # Calculate the scale used in display_preview
        img_width, img_height = original_image.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        
        # Calculate the actual rendered image size on canvas
        rendered_width = int(img_width * scale)
        rendered_height = int(img_height * scale)
        
        # Calculate the offset due to centering the image on canvas
        offset_x = (canvas_width - rendered_width) // 2
        offset_y = (canvas_height - rendered_height) // 2
        
        # Convert canvas coordinates (relative to centered image) to image coordinates
        img_x = int((event.x - offset_x) / scale)
        img_y = int((event.y - offset_y) / scale)
        
        # Check if click is within image bounds
        if 0 <= img_x < img_width and 0 <= img_y < img_height:
            # Set custom position
            self.custom_watermark_x = img_x
            self.custom_watermark_y = img_y
            
            # Set the position to custom
            self.watermark_position_var.set("custom")
            
            # Update preview immediately
            self.display_preview()
            
            # Start dragging immediately since we just clicked and set the position
            self.is_dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            # Calculate initial watermark position in canvas coordinates (relative to image area)
            self.watermark_start_x = self.custom_watermark_x * scale + offset_x
            self.watermark_start_y = self.custom_watermark_y * scale + offset_y
    
    def on_watermark_drag_start(self, event):
        """开始拖拽水印 - This will be called when mouse button is pressed on canvas if not already dragging"""
        if not self.watermark_enabled_var.get() or self.watermark_position_var.get() != "custom":
            return
        
        # If we're not already dragging (e.g., from a click event), set up the drag
        if not self.is_dragging:
            self.is_dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            # Get the currently displayed image to get the scale
            image_path = self.image_paths[self.current_image_index]
            original_image = Image.open(image_path)
            
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 600
                canvas_height = 400
            
            img_width, img_height = original_image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            # Calculate the actual rendered image size on canvas
            rendered_width = int(img_width * scale)
            rendered_height = int(img_height * scale)
            
            # Calculate the offset due to centering the image on canvas
            offset_x = (canvas_width - rendered_width) // 2
            offset_y = (canvas_height - rendered_height) // 2
            
            # Initialize the start position if we have custom watermark coordinates
            if self.custom_watermark_x is not None and self.custom_watermark_y is not None:
                # Store the current watermark position in canvas coordinates (relative to image area)
                self.watermark_start_x = self.custom_watermark_x * scale + offset_x
                self.watermark_start_y = self.custom_watermark_y * scale + offset_y
            else:
                # If no custom position yet, set it to current mouse position relative to image area
                self.custom_watermark_x = int((event.x - offset_x) / scale)
                self.custom_watermark_y = int((event.y - offset_y) / scale)
                # Calculate the start position based on the new coordinates
                self.watermark_start_x = self.custom_watermark_x * scale + offset_x
                self.watermark_start_y = self.custom_watermark_y * scale + offset_y
    
    def on_watermark_drag(self, event):
        """拖拽水印中"""
        if not self.watermark_enabled_var.get() or self.watermark_position_var.get() != "custom" or not self.is_dragging:
            return
        
        # Calculate scale and offsets
        image_path = self.image_paths[self.current_image_index]
        original_image = Image.open(image_path)
        
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 600
            canvas_height = 400
        
        img_width, img_height = original_image.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        
        # Calculate the actual rendered image size on canvas
        rendered_width = int(img_width * scale)
        rendered_height = int(img_height * scale)
        
        # Calculate the offset due to centering the image on canvas
        offset_x = (canvas_width - rendered_width) // 2
        offset_y = (canvas_height - rendered_height) // 2
        
        # Calculate new image coordinates directly from current mouse position
        # This ensures the watermark follows the mouse immediately and precisely
        new_img_x = int((event.x - offset_x) / scale)
        new_img_y = int((event.y - offset_y) / scale)
        
        # Ensure the new coordinates stay within image bounds
        new_img_x = max(0, min(new_img_x, img_width - 1))  # -1 to account for text width
        new_img_y = max(0, min(new_img_y, img_height - 1))  # -1 to account for text height
        
        # Update custom position
        self.custom_watermark_x = new_img_x
        self.custom_watermark_y = new_img_y
        
        # Update preview immediately to provide visual feedback during drag
        self.display_preview()
    
    def on_watermark_drag_end(self, event):
        """结束拖拽水印"""
        self.is_dragging = False
        # Reset drag start variables
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.watermark_start_x = 0
        self.watermark_start_y = 0

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
            
            # 应用实时水印（如果启用）
            if self.watermark_enabled_var.get():
                from photowatermark.models.image_processor import ImageProcessor
                processor = ImageProcessor()
                
                # Check if we're using custom drag-and-drop position
                current_position = self.watermark_position_var.get()
                if current_position == "custom" and self.custom_watermark_x is not None and self.custom_watermark_y is not None:
                    # For custom positioning, we'll pass the exact coordinates through a special method
                    # Since the processor doesn't support exact coordinates yet, we'll need to enhance it
                    watermark_settings = {
                        'text': self.watermark_text_var.get(),
                        'transparency': self.watermark_transparency_var.get(),
                        'position': 'custom',  # Use custom position
                        'custom_x': self.custom_watermark_x,
                        'custom_y': self.custom_watermark_y,
                        'font_size': self.watermark_font_size_var.get(),  # 动态字体大小
                        'font_name': self.watermark_font_var.get(),  # 字体名称
                        'color': (255, 255, 255)  # 默认白色
                    }
                else:
                    # Use preset position
                    watermark_settings = {
                        'text': self.watermark_text_var.get(),
                        'transparency': self.watermark_transparency_var.get(),
                        'position': current_position,
                        'font_size': self.watermark_font_size_var.get(),  # 动态字体大小
                        'font_name': self.watermark_font_var.get(),  # 字体名称
                        'color': (255, 255, 255)  # 默认白色
                    }
                
                # 应用水印到图片（但不改变原始图片）
                image_with_watermark = processor.add_watermark_to_image(image.copy(), watermark_settings)
                preview_image = image_with_watermark
            else:
                preview_image = image
            
            # 获取预览画布的当前尺寸
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            # 如果画布尺寸不可用，则设置默认尺寸
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 600
                canvas_height = 400
                self.preview_canvas.config(width=canvas_width, height=canvas_height)
            
            # 保持宽高比缩放
            img_width, img_height = preview_image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # 兼容不同版本的Pillow
            try:
                preview_image = preview_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            except AttributeError:
                # 对于旧版本的Pillow
                preview_image = preview_image.resize((new_width, new_height), Image.LANCZOS)
            
            # 将图片转换为tkinter可以显示的格式
            self.current_image = ImageTk.PhotoImage(preview_image)
            
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
            
            # 绑定鼠标事件用于水印拖拽功能
            # Use Button-1 for click to set initial position, B1-Motion for drag
            self.preview_canvas.bind("<Button-1>", self.on_watermark_canvas_click)
            self.preview_canvas.bind("<B1-Motion>", self.on_watermark_drag)  # Changed from Button1-Motion to B1-Motion
            self.preview_canvas.bind("<ButtonRelease-1>", self.on_watermark_drag_end)
            
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
            'watermark_font_size': self.watermark_font_size_var.get(),
            'watermark_font_name': self.watermark_font_var.get(),  # 字体名称
            'watermark_color': (255, 255, 255)  # Default white color
        }
        
        # Add custom watermark coordinates if in custom position mode
        if self.watermark_position_var.get() == "custom" and self.custom_watermark_x is not None and self.custom_watermark_y is not None:
            settings['watermark_custom_x'] = self.custom_watermark_x
            settings['watermark_custom_y'] = self.custom_watermark_y
        
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
                'watermark_font_size': self.watermark_font_size_var.get(),
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
                            'font_name': settings.get('watermark_font_name', 'Arial'),  # 字体名称
                            'color': settings.get('watermark_color', (255, 255, 255))
                        }
                        
                        # Add custom coordinates if in custom position mode
                        if (settings.get('watermark_position') == "custom" and 
                            'watermark_custom_x' in settings and 
                            'watermark_custom_y' in settings):
                            watermark_settings['custom_x'] = settings['watermark_custom_x']
                            watermark_settings['custom_y'] = settings['watermark_custom_y']
                        
                        # Apply watermark to the image
                        image = processor.add_watermark_to_image(image, watermark_settings)
                    
                    # 处理图片以准备导出
                    image = processor.process_image_for_export(
                        image, 
                        os.path.splitext(output_path)[1], 
                        settings.get('quality', 95)
                    )
                    
                    # 处理图片格式转换
                    _, ext = os.path.splitext(output_path)
                    ext = ext.lower()
                    
                    # 保存图片
                    if ext in ['.jpg', '.jpeg']:
                        # JPEG不支持透明通道，转换为RGB
                        if image.mode in ('RGBA', 'LA', 'P'):
                            if image.mode == 'P':
                                image = image.convert("RGBA")
                            image_to_save = image.convert("RGB")
                        else:
                            image_to_save = image
                        # 对于JPEG格式，使用用户设置的质量
                        image_to_save.save(output_path, "JPEG", quality=settings.get('quality', 95), exif=image.info.get('exif', b''))
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
    
    def _process_and_save_image(self, input_path, output_path, settings):
        """处理单张图片：应用水印、调整尺寸、保存"""
        from photowatermark.models.image_processor import ImageProcessor
        processor = ImageProcessor()
        
        # 打开图片
        image = Image.open(input_path)
        
        # 如果启用水印，应用水印
        if settings.get('watermark_enabled', False):
            # 准备水印设置
            watermark_settings = {
                'text': settings.get('watermark_text', 'Sample Text'),
                'transparency': settings.get('watermark_transparency', DEFAULT_WATERMARK_TRANSPARENCY),
                'position': settings.get('watermark_position', DEFAULT_WATERMARK_POSITION),
                'font_size': settings.get('watermark_font_size', DEFAULT_WATERMARK_SIZE),
                'font_name': settings.get('watermark_font_name', 'Arial'),  # 字体名称
                'color': settings.get('watermark_color', DEFAULT_WATERMARK_COLOR)
            }
            
            # 如果是自定义位置，添加坐标
            if (settings.get('watermark_position') == "custom" and 
                'watermark_custom_x' in settings and 
                'watermark_custom_y' in settings):
                watermark_settings['custom_x'] = settings['watermark_custom_x']
                watermark_settings['custom_y'] = settings['watermark_custom_y']
            
            # 应用水印到图片
            image = processor.add_watermark_to_image(image, watermark_settings)
        
        # 根据设置调整图片尺寸（在水印添加后）
        original_image = Image.open(input_path)  # Reopen to get original size
        original_width, original_height = original_image.size
        image = processor.resize_image(
            image, 
            settings.get('resize_option'), 
            settings.get('resize_value'),
            original_width,
            original_height
        )
        
        # 处理图片以准备导出
        image = processor.process_image_for_export(
            image, 
            os.path.splitext(output_path)[1], 
            settings.get('quality', 95)
        )
        
        # 处理图片格式转换并保存
        _, ext = os.path.splitext(output_path)
        ext = ext.lower()
        
        if ext in ['.jpg', '.jpeg']:
            # JPEG不支持透明通道，转换为RGB
            if image.mode in ('RGBA', 'LA', 'P'):
                if image.mode == 'P':
                    image = image.convert("RGBA")
                image_to_save = image.convert("RGB")
            else:
                image_to_save = image
            # 对于JPEG格式，使用用户设置的质量
            image_to_save.save(output_path, "JPEG", quality=settings.get('quality', 95), exif=image.info.get('exif', b''))
        elif ext == '.png':
            # 对于PNG格式，保存时保留透明通道
            image.save(output_path, "PNG", exif=image.info.get('exif', b''))
        else:
            # 对于其他格式，按原样保存
            image.save(output_path, exif=image.info.get('exif', b''))
    
    def save_config(self):
        """保存当前水印配置"""
        try:
            # 确保配置目录存在
            os.makedirs(self.configs_dir, exist_ok=True)
            
            # 获取当前配置名称
            config_name = self.config_name_var.get().strip()
            if not config_name:
                messagebox.showwarning("警告", "请输入配置名称")
                return
            
            # 获取当前水印设置
            config_data = {
                'watermark_enabled': self.watermark_enabled_var.get(),
                'watermark_text': self.watermark_text_var.get(),
                'watermark_transparency': self.watermark_transparency_var.get(),
                'watermark_position': self.watermark_position_var.get(),
                'watermark_font_size': self.watermark_font_size_var.get(),
                'watermark_font_name': self.watermark_font_var.get(),  # 字体名称
                'watermark_color': (255, 255, 255),  # 目前颜色是固定的，后续可以扩展
                'custom_watermark_x': self.custom_watermark_x,
                'custom_watermark_y': self.custom_watermark_y
            }
            
            # 生成配置文件路径
            config_file = os.path.join(self.configs_dir, f"{config_name}.json")
            
            # 保存配置到文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", f"配置已保存为: {config_name}")
            
        except Exception as e:
            error_msg = f"保存配置时发生错误: {str(e)}"
            show_error_message(self.root, "错误", error_msg)
    
    def load_config(self):
        """加载水印配置"""
        try:
            # 确保配置目录存在
            os.makedirs(self.configs_dir, exist_ok=True)
            
            # 让用户选择配置文件
            config_file = filedialog.askopenfilename(
                title="选择配置文件",
                initialdir=self.configs_dir,
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not config_file:
                return  # 用户取消了选择
            
            # 读取配置文件
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 应用配置
            if 'watermark_enabled' in config_data:
                self.watermark_enabled_var.set(config_data['watermark_enabled'])
                
            if 'watermark_text' in config_data:
                self.watermark_text_var.set(config_data['watermark_text'])
                
            if 'watermark_transparency' in config_data:
                self.watermark_transparency_var.set(config_data['watermark_transparency'])
                
            if 'watermark_position' in config_data:
                self.watermark_position_var.set(config_data['watermark_position'])
                
            if 'watermark_font_size' in config_data:
                self.watermark_font_size_var.set(config_data['watermark_font_size'])
                
            if 'watermark_font_name' in config_data:
                self.watermark_font_var.set(config_data['watermark_font_name'])
                
            # 应用自定义坐标
            if 'custom_watermark_x' in config_data:
                self.custom_watermark_x = config_data['custom_watermark_x']
            if 'custom_watermark_y' in config_data:
                self.custom_watermark_y = config_data['custom_watermark_y']
            
            # 重新启用/禁用水印控件
            enabled = self.watermark_enabled_var.get()
            state = 'normal' if enabled else 'disabled'
            self.watermark_text_entry.config(state=state)
            
            # 更新预览
            self.display_preview()
            
            # 提取并显示配置名称（去掉路径和扩展名）
            config_name = os.path.basename(config_file)
            if config_name.endswith('.json'):
                config_name = config_name[:-5]
            self.config_name_var.set(config_name)
            
            messagebox.showinfo("成功", f"配置已加载: {config_name}")
            
        except Exception as e:
            error_msg = f"加载配置时发生错误: {str(e)}"
            show_error_message(self.root, "错误", error_msg)
    
    def delete_config(self):
        """删除水印配置"""
        try:
            # 确保配置目录存在
            os.makedirs(self.configs_dir, exist_ok=True)
            
            # 让用户选择要删除的配置文件
            config_file = filedialog.askopenfilename(
                title="选择要删除的配置文件",
                initialdir=self.configs_dir,
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not config_file:
                return  # 用户取消了选择
            
            # 获取配置文件名用于确认对话框
            config_name = os.path.basename(config_file)
            if config_name.endswith('.json'):
                config_name = config_name[:-5]
            
            # 确认删除操作
            result = messagebox.askyesno("确认删除", f"确定要删除配置 '{config_name}' 吗？此操作不可撤销。")
            if not result:
                return  # 用户取消删除
            
            # 删除配置文件
            os.remove(config_file)
            messagebox.showinfo("成功", f"配置已删除: {config_name}")
            
        except Exception as e:
            error_msg = f"删除配置时发生错误: {str(e)}"
            show_error_message(self.root, "错误", error_msg)
    
    def save_app_state(self):
        """保存应用程序状态"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.app_state_file), exist_ok=True)
            
            # 获取当前应用程序状态
            app_state = {
                'window_width': self.root.winfo_width(),
                'window_height': self.root.winfo_height(),
                'window_x': self.root.winfo_x(),
                'window_y': self.root.winfo_y(),
                'watermark_enabled': self.watermark_enabled_var.get() if self.watermark_enabled_var else False,
                'watermark_text': self.watermark_text_var.get() if self.watermark_text_var else 'Sample Text',
                'watermark_transparency': self.watermark_transparency_var.get() if self.watermark_transparency_var else 50,
                'watermark_position': self.watermark_position_var.get() if self.watermark_position_var else 'bottom-right',
                'watermark_font_size': self.watermark_font_size_var.get() if self.watermark_font_size_var else 30,
                'watermark_font_name': self.watermark_font_var.get() if self.watermark_font_var else 'Arial',  # 字体名称
                'custom_watermark_x': self.custom_watermark_x,
                'custom_watermark_y': self.custom_watermark_y,
                'naming_rule': self.naming_var.get() if self.naming_var else '保留原名',
                'naming_value': self.naming_entry.get() if self.naming_entry else '',
                'format_rule': self.format_var.get() if self.format_var else '原格式',
                'quality': self.quality_var.get() if self.quality_var else 95,
                'resize_option': self.resize_var.get() if self.resize_var else '原图尺寸',
                'resize_value': self.resize_entry.get() if self.resize_entry else ''
            }
            
            # 保存状态到文件
            with open(self.app_state_file, 'w', encoding='utf-8') as f:
                json.dump(app_state, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存应用程序状态时发生错误: {str(e)}")
    
    def load_app_state(self):
        """加载应用程序状态"""
        try:
            if not os.path.exists(self.app_state_file):
                return  # 如果状态文件不存在，则使用默认值
            
            # 从文件加载状态
            with open(self.app_state_file, 'r', encoding='utf-8') as f:
                app_state = json.load(f)
            
            # 应用窗口状态
            if 'window_width' in app_state and 'window_height' in app_state:
                width = app_state['window_width']
                height = app_state['window_height']
                # 确保窗口大小在合理范围内
                width = max(800, min(width, 1920))
                height = max(600, min(height, 1080))
                self.root.geometry(f"{width}x{height}")
            
            # 应用窗口位置
            if 'window_x' in app_state and 'window_y' in app_state:
                x = app_state['window_x']
                y = app_state['window_y']
                # 确保窗口位置在屏幕范围内
                x = max(0, x)
                y = max(0, y)
                self.root.geometry(f"+{x}+{y}")
            
            # 应用水印设置
            if 'watermark_enabled' in app_state:
                self.watermark_enabled_var.set(app_state['watermark_enabled'])
                
            if 'watermark_text' in app_state:
                self.watermark_text_var.set(app_state['watermark_text'])
                
            if 'watermark_transparency' in app_state:
                self.watermark_transparency_var.set(app_state['watermark_transparency'])
                
            if 'watermark_position' in app_state:
                self.watermark_position_var.set(app_state['watermark_position'])
                
            if 'watermark_font_size' in app_state:
                self.watermark_font_size_var.set(app_state['watermark_font_size'])
                
            if 'watermark_font_name' in app_state:
                self.watermark_font_var.set(app_state['watermark_font_name'])
                
            # 应用自定义坐标
            if 'custom_watermark_x' in app_state:
                self.custom_watermark_x = app_state['custom_watermark_x']
            if 'custom_watermark_y' in app_state:
                self.custom_watermark_y = app_state['custom_watermark_y']
            
            # 应用导出设置
            if 'naming_rule' in app_state:
                self.naming_var.set(app_state['naming_rule'])
                
            if 'naming_value' in app_state:
                self.naming_entry.delete(0, tk.END)
                self.naming_entry.insert(0, app_state['naming_value'])
                
            if 'format_rule' in app_state:
                self.format_var.set(app_state['format_rule'])
                
            if 'quality' in app_state:
                self.quality_var.set(app_state['quality'])
                
            if 'resize_option' in app_state:
                self.resize_var.set(app_state['resize_option'])
                
            if 'resize_value' in app_state:
                self.resize_entry.delete(0, tk.END)
                self.resize_entry.insert(0, app_state['resize_value'])
                
            # 更新UI以反映新设置
            self.on_naming_change()
            self.on_resize_change()
            self.on_watermark_enabled_change()
            
        except Exception as e:
            print(f"加载应用程序状态时发生错误: {str(e)}")
    
    def export_current_image(self):
        """导出当前选中的图片"""
        if not self.image_paths or self.current_image_index >= len(self.image_paths):
            messagebox.showwarning("警告", "没有选中的图片。")
            return
        
        # 选择输出目录
        output_dir = filedialog.askdirectory(title="选择导出目录")
        if not output_dir:
            return  # 用户取消了操作
        
        # 确保输出目录不是输入图片的目录（完全禁止）
        current_image_path = self.image_paths[self.current_image_index]
        input_dir = os.path.dirname(current_image_path)
        
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
        
        # 准备设置字典
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
            'watermark_font_size': self.watermark_font_size_var.get(),
            'watermark_font_name': self.watermark_font_var.get(),  # 字体名称
            'watermark_color': (255, 255, 255)  # Default white color
        }
        
        # 如果使用自定义位置，则添加自定义坐标
        if (self.watermark_position_var.get() == "custom" and 
            self.custom_watermark_x is not None and 
            self.custom_watermark_y is not None):
            settings['watermark_custom_x'] = self.custom_watermark_x
            settings['watermark_custom_y'] = self.custom_watermark_y
        
        # 只导出当前选中的图片
        current_image_path = self.image_paths[self.current_image_index]
        
        try:
            # 使用通用的导出函数来导出单张图片
            from photowatermark.models.image_processor import ImageProcessor
            processor = ImageProcessor()
            
            # 生成输出文件名
            output_path = processor.generate_output_filename(
                current_image_path, 
                output_dir,
                settings.get('naming_rule'),
                settings.get('naming_value'),
                settings.get('format_rule')
            )
            
            # 使用通用的导出处理函数
            self._process_and_save_image(current_image_path, output_path, settings)
            
            messagebox.showinfo("成功", f"当前图片已导出到:\n{output_path}")
            
        except Exception as e:
            error_msg = f"导出当前图片时发生错误: {str(e)}"
            show_error_message(self.root, "错误", error_msg)
    
    def on_closing(self):
        """窗口关闭时的处理"""
        # 保存当前应用程序状态
        self.save_app_state()
        # 销毁窗口
        self.root.destroy()

    def _export_process(self, output_dir):
        """在后台线程中执行导出操作"""
        try:
            success_count = 0
            for i, img_path in enumerate(self.image_paths):
                try:
                    # 构建设置字典，用于调用通用处理函数
                    current_settings = {
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
                        'watermark_font_size': self.watermark_font_size_var.get(),
                        'watermark_color': DEFAULT_WATERMARK_COLOR  # Default white color
                    }
                    
                    # 如果使用自定义位置，则添加自定义坐标
                    if (self.watermark_position_var.get() == "custom" and 
                        self.custom_watermark_x is not None and 
                        self.custom_watermark_y is not None):
                        current_settings['watermark_custom_x'] = self.custom_watermark_x
                        current_settings['watermark_custom_y'] = self.custom_watermark_y
                    
                    # 生成输出文件名
                    from photowatermark.models.image_processor import ImageProcessor
                    processor = ImageProcessor()
                    output_path = processor.generate_output_filename(
                        img_path, 
                        output_dir,
                        current_settings.get('naming_rule'),
                        current_settings.get('naming_value'),
                        current_settings.get('format_rule')
                    )
                    
                    # 使用通用的处理函数
                    self._process_and_save_image(img_path, output_path, current_settings)
                    
                    success_count += 1
                except Exception as e:
                    print(f"导出文件失败 {img_path}: {str(e)}")
            
            # 在主线程中显示完成消息
            self.root.after(0, lambda: messagebox.showinfo("完成", f"导出完毕！成功导出 {success_count} 个文件。"))
        except Exception as e:
            error_msg = f"导出过程中发生错误: {str(e)}"
            self.root.after(0, lambda: show_error_message(self.root, "错误", error_msg))