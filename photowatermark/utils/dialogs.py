"""
Dialog utilities for the PhotoWatermark-AI4SE application.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext


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