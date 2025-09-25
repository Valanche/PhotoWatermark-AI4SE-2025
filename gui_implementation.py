"""
PhotoWatermark-AI4SE GUI Implementation
迭代二：实现文件处理功能
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import os
import threading
from typing import List

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("警告: 未安装tkinterdnd2库，拖拽功能将不可用。请运行 'pip install tkinterdnd2' 来启用此功能。")


class CopyableMessageBox:
    """可复制的错误消息对话框"""
    def __init__(self, parent, title, message):
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("600x400")
        self.top.transient(parent)
        self.top.grab_set()
        
        # 创建滚动文本框
        text_frame = ttk.Frame(self.top)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        self.text_widget.insert(tk.END, message)
        self.text_widget.config(state=tk.DISABLED)  # 设置为只读
        
        # 复制按钮
        button_frame = ttk.Frame(self.top)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        copy_btn = ttk.Button(button_frame, text="复制到剪贴板", command=self.copy_to_clipboard)
        copy_btn.pack(side=tk.LEFT)
        
        ok_btn = ttk.Button(button_frame, text="确定", command=self.top.destroy)
        ok_btn.pack(side=tk.RIGHT)
    
    def copy_to_clipboard(self):
        """复制文本到剪贴板"""
        self.top.clipboard_clear()
        self.top.clipboard_append(self.text_widget.get(1.0, tk.END))
        self.top.update()  # 更新剪贴板


def show_error_message(parent, title, message):
    """显示可复制的错误消息"""
    CopyableMessageBox(parent, title, message)


class PhotoWatermarkGUI:
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
        self.thumbnail_size = (80, 80)
        # 存储缩略图组件的引用
        self.thumbnail_widgets = []
        
        self.setup_ui()
        
        # 设置拖拽事件（如果支持）
        if HAS_DND:
            self.setup_drag_drop()
    
    def on_thumbnail_frame_configure(self, event):
        """当缩略图框架大小改变时更新滚动区域"""
        self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        """当画布大小改变时更新框架宽度"""
        canvas_width = event.width
        self.thumbnail_canvas.itemconfig(self.thumbnail_frame_id, width=canvas_width)
    
    def create_thumbnail(self, image_path):
        """为指定图片路径创建缩略图"""
        try:
            image = Image.open(image_path)
            image_copy = image.copy()  # 避免关闭原图
            image_copy.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
            return ImageTk.PhotoImage(image_copy)
        except AttributeError:
            # 对于旧版本的Pillow
            image = Image.open(image_path)
            image_copy = image.copy()
            image_copy.thumbnail(self.thumbnail_size, Image.LANCZOS)
            return ImageTk.PhotoImage(image_copy)
        except Exception:
            # 如果无法创建缩略图，返回占位符
            placeholder = Image.new('RGB', self.thumbnail_size, (200, 200, 200))
            return ImageTk.PhotoImage(placeholder)
    
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
    
    def on_resize_change(self, event=None):
        """当尺寸调整方式改变时"""
        if self.resize_var.get() in ["按比例缩放", "指定宽度", "指定高度"]:
            self.resize_entry.config(state='enabled')
        else:
            self.resize_entry.config(state='disabled')
            self.resize_entry.delete(0, tk.END)
    
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
        
        # 创建列表框和滚动条
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # 使用Canvas和Frame组合来创建带缩略图的列表
        self.thumbnail_canvas = tk.Canvas(list_container, bg='white')
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.thumbnail_canvas.yview)
        
        # 创建一个内部框架来容纳缩略图项目
        self.thumbnail_frame = ttk.Frame(self.thumbnail_canvas)
        self.thumbnail_frame_id = self.thumbnail_canvas.create_window((0, 0), window=self.thumbnail_frame, anchor="nw")
        
        # 配置滚动功能
        self.thumbnail_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.thumbnail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 存储缩略图引用，防止被垃圾回收
        self.thumbnail_images = []
        
        # 绑定配置事件以更新滚动区域
        self.thumbnail_frame.bind("<Configure>", self.on_thumbnail_frame_configure)
        self.thumbnail_canvas.bind("<Configure>", self.on_canvas_configure)
        
        # 预定义缩略图大小
        self.thumbnail_size = (80, 80)
        
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
        ttk.Label(resize_frame, text="%").pack(side=tk.LEFT)
        
        # 导出按钮
        export_btn = ttk.Button(export_frame, text="导出图片", command=self.export_images)
        export_btn.pack(pady=5)
    
    def setup_drag_drop(self):
        """设置拖拽功能"""
        # 为预览画布设置拖拽事件
        self.preview_canvas.drop_target_register(DND_FILES)
        self.preview_canvas.dnd_bind('<<Drop>>', self.on_drop)
        
        # 为缩略图画布设置拖拽事件
        self.thumbnail_canvas.drop_target_register(DND_FILES)
        self.thumbnail_canvas.dnd_bind('<<Drop>>', self.on_drop)
        
        # 为缩略图框架设置拖拽事件
        self.thumbnail_frame.drop_target_register(DND_FILES)
        self.thumbnail_frame.dnd_bind('<<Drop>>', self.on_drop)
    
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
            # 创建缩略图项目
            self.add_thumbnail_item(path)
        
        # 如果这是第一次添加图片，自动选择第一张
        if len(self.image_paths) == len(new_paths):
            self.current_image_index = 0
            self.select_thumbnail_item(0)
            self.display_preview()
    
    def add_thumbnail_item(self, image_path):
        """添加单个缩略图项目"""
        # 创建缩略图
        thumbnail_img = self.create_thumbnail(image_path)
        self.thumbnail_images.append(thumbnail_img)  # 保持引用防止被垃圾回收
        
        # 创建缩略图项的框架
        item_frame = ttk.Frame(self.thumbnail_frame, relief=tk.RAISED, borderwidth=1)
        item_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # 创建图片标签
        img_label = tk.Label(item_frame, image=thumbnail_img, bd=0)
        img_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 创建文件名标签
        filename = os.path.basename(image_path)
        name_label = tk.Label(item_frame, text=filename, anchor='w')
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=5)
        
        # 获取当前索引
        idx = len(self.thumbnail_widgets)
        
        # 绑定点击事件
        def on_click(e, index=idx):
            self.select_thumbnail_item(index)
        
        item_frame.bind("<Button-1>", on_click)
        img_label.bind("<Button-1>", on_click)
        name_label.bind("<Button-1>", on_click)
        
        # 存储组件引用
        self.thumbnail_widgets.append({
            'frame': item_frame,
            'img_label': img_label,
            'name_label': name_label,
            'path': image_path
        })
        
        # 更新滚动区域
        self.thumbnail_frame.update_idletasks()
        self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))
    
    def select_thumbnail_item(self, index):
        """选择指定索引的缩略图项"""
        # 重置所有项的背景色
        for widget_info in self.thumbnail_widgets:
            widget_info['frame'].configure(relief=tk.RAISED)
        
        # 设置选中项的背景色
        if 0 <= index < len(self.thumbnail_widgets):
            self.thumbnail_widgets[index]['frame'].configure(relief=tk.SUNKEN)
            self.current_image_index = index
            self.display_preview()
    
    # 删除这个方法，因为我们不再使用Listbox的事件
    
    def display_preview(self):
        """在预览区域显示当前图片"""
        if not self.image_paths or self.current_image_index >= len(self.image_paths):
            return
        
        try:
            image_path = self.image_paths[self.current_image_index]
            image = Image.open(image_path)
            
            # 调整图片大小以适应预览区域
            canvas_width = max(self.preview_canvas.winfo_width(), 600)  # 确保有默认大小
            canvas_height = max(self.preview_canvas.winfo_height(), 400)
            
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
            
        except Exception as e:
            error_msg = f"无法加载图片 {image_path}: {str(e)}"
            show_error_message(self.root, "错误", error_msg)
    
    def export_images(self):
        """导出图片"""
        if not self.image_paths:
            messagebox.showwarning("警告", "没有要导出的图片。")
            return
        
        output_dir = filedialog.askdirectory(title="选择导出目录")
        if not output_dir:
            return  # 用户取消了操作
        
        # 确保输出目录不是输入图片的目录
        input_dir = os.path.dirname(self.image_paths[0]) if self.image_paths else ""
        try:
            if input_dir and os.path.samefile(output_dir, input_dir):
                if not messagebox.askyesno("确认", "导出目录与输入目录相同，可能会覆盖原图。是否继续？"):
                    return
        except OSError:
            # 如果无法比较路径（例如在不同驱动器上），则继续
            pass
        
        # 在新线程中执行导出以避免界面冻结
        threading.Thread(target=self._export_process, args=(output_dir,), daemon=True).start()
    
    def generate_output_filename(self, input_path, output_dir):
        """根据用户设置生成输出文件名"""
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        
        naming_rule = self.naming_var.get()
        if naming_rule == "添加前缀":
            prefix = self.naming_entry.get().strip()
            if prefix:
                name = prefix + name
        elif naming_rule == "添加后缀":
            suffix = self.naming_entry.get().strip()
            if suffix:
                name = name + suffix
        # "保留原名"选项不需要更改
        
        # 根据输出格式决定扩展名
        format_rule = self.format_var.get()
        if format_rule == "JPEG":
            ext = ".jpg"
        elif format_rule == "PNG":
            ext = ".png"
        # "原格式"选项保持原扩展名
        
        output_path = os.path.join(output_dir, f"{name}{ext}")
        return output_path
    
    def resize_image(self, image):
        """根据用户设置调整图片尺寸"""
        resize_option = self.resize_var.get()
        
        if resize_option == "原图尺寸":
            return image
        else:
            try:
                value = int(self.resize_entry.get()) if self.resize_entry.get() else 100
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
    
    def _export_process(self, output_dir):
        """在后台线程中执行导出操作"""
        try:
            success_count = 0
            for i, img_path in enumerate(self.image_paths):
                try:
                    # 生成输出文件名
                    output_path = self.generate_output_filename(img_path, output_dir)
                    
                    # 打开图片
                    image = Image.open(img_path)
                    
                    # 根据设置调整图片尺寸
                    image = self.resize_image(image)
                    
                    # 获取文件扩展名以确定保存格式
                    _, ext = os.path.splitext(output_path)
                    ext = ext.lower()
                    
                    # 如果需要转换格式，确保图片模式正确
                    if ext in ['.jpg', '.jpeg'] and image.mode in ('RGBA', 'LA', 'P'):
                        # JPEG不支持透明通道，转换为RGB
                        if image.mode == 'P':
                            image = image.convert("RGBA")
                        image = image.convert("RGB")
                    
                    # 保存图片
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


def main():
    app = PhotoWatermarkGUI()
    app.root.mainloop()


if __name__ == "__main__":
    main()