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
        self.thumbnail_size = (100, 100)
        
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
        
        # 创建列表框和滚动条
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.image_listbox = tk.Listbox(list_container)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.image_listbox.yview)
        self.image_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览")
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas用于显示预览图
        self.preview_canvas = tk.Canvas(preview_frame, bg='gray')
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 底部导出按钮
        export_frame = ttk.Frame(main_frame)
        export_frame.pack(fill=tk.X, pady=(10, 0))
        
        export_btn = ttk.Button(export_frame, text="导出图片", command=self.export_images)
        export_btn.pack()
    
    def setup_drag_drop(self):
        """设置拖拽功能"""
        # 为预览画布设置拖拽事件
        self.preview_canvas.drop_target_register(DND_FILES)
        self.preview_canvas.dnd_bind('<<Drop>>', self.on_drop)
        
        # 为图片列表设置拖拽事件
        self.image_listbox.drop_target_register(DND_FILES)
        self.image_listbox.dnd_bind('<<Drop>>', self.on_drop)
    
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
            # 显示文件名（不包括路径）到列表框
            filename = os.path.basename(path)
            self.image_listbox.insert(tk.END, filename)
        
        # 如果这是第一次添加图片，自动选择第一张
        if len(self.image_paths) == len(new_paths):
            self.current_image_index = 0
            self.image_listbox.selection_set(0)
            self.display_preview()
    
    def on_image_select(self, event):
        """当在列表中选择图片时"""
        selection = self.image_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_image_index = index
            self.display_preview()
    
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
    
    def _export_process(self, output_dir):
        """在后台线程中执行导出操作"""
        try:
            success_count = 0
            for i, img_path in enumerate(self.image_paths):
                try:
                    # 生成输出文件名
                    filename = os.path.basename(img_path)
                    name, ext = os.path.splitext(filename)
                    
                    # 简单的命名规则（保留原文件名），实际应用中可以提供更多选项
                    output_path = os.path.join(output_dir, f"{name}_watermarked{ext}")
                    
                    # 复制图片到输出目录（在完整实现中，这里会添加水印）
                    image = Image.open(img_path)
                    
                    # 保存时保留EXIF信息
                    image.save(output_path, exif=image.info.get('exif', b''))
                    
                    success_count += 1
                except Exception as e:
                    error_msg = f"导出文件失败 {img_path}: {str(e)}"
                    print(error_msg)  # 同时打印到控制台
            
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