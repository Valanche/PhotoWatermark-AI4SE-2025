"""
Thumbnail list widget for the PhotoWatermark-AI4SE application.
"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os


class ThumbnailList:
    def __init__(self, parent, on_select_callback=None):
        self.parent = parent
        self.on_select_callback = on_select_callback
        self.image_paths = []
        self.thumbnail_widgets = []
        self.thumbnail_images = []  # Store references to prevent garbage collection
        self.thumbnail_size = (80, 80)
        self.current_selection = -1
        
        # Create UI elements
        self.canvas = tk.Canvas(parent, bg='white')
        self.scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        
        # Create a frame inside the canvas to hold thumbnails
        self.frame = ttk.Frame(self.canvas)
        self.frame_id = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        
        # Configure scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack elements
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events for scrolling
        self.frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
    def on_frame_configure(self, event):
        """当缩略图框架大小改变时更新滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def on_canvas_configure(self, event):
        """当画布大小改变时更新框架宽度"""
        canvas_width = event.width
        self.canvas.itemconfig(self.frame_id, width=canvas_width)

    def add_thumbnail(self, image_path):
        """添加单个缩略图项目"""
        # Store the image path
        self.image_paths.append(image_path)
        
        # Create thumbnail
        thumbnail_img = self.create_thumbnail(image_path)
        self.thumbnail_images.append(thumbnail_img)  # Keep reference to prevent garbage collection
        
        # Create thumbnail item frame
        item_frame = ttk.Frame(self.frame, relief=tk.RAISED, borderwidth=1)
        item_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Create image label
        img_label = tk.Label(item_frame, image=thumbnail_img, bd=0)
        img_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Create filename label
        filename = os.path.basename(image_path)
        name_label = tk.Label(item_frame, text=filename, anchor='w')
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=5)
        
        # Get current index
        idx = len(self.thumbnail_widgets)
        
        # Bind click event
        def on_click(e, index=idx):
            self.select_item(index)
        
        item_frame.bind("<Button-1>", on_click)
        img_label.bind("<Button-1>", on_click)
        name_label.bind("<Button-1>", on_click)
        
        # Store widget references
        widget_info = {
            'frame': item_frame,
            'img_label': img_label,
            'name_label': name_label,
            'path': image_path
        }
        self.thumbnail_widgets.append(widget_info)
        
        # Update scroll region
        self.frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def create_thumbnail(self, image_path):
        """Create a thumbnail for the given image path"""
        try:
            image = Image.open(image_path)
            image_copy = image.copy()
            # 兼容不同版本的PIL
            try:
                image_copy.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            except AttributeError:
                # 对于旧版本的PIL
                image_copy.thumbnail(self.thumbnail_size, Image.LANCZOS)
            return ImageTk.PhotoImage(image_copy)
        except Exception:
            # Return placeholder if thumbnail creation fails
            placeholder = Image.new('RGB', self.thumbnail_size, (200, 200, 200))
            return ImageTk.PhotoImage(placeholder)

    def select_item(self, index):
        """Select the thumbnail at the given index"""
        # Reset background color of all items
        for widget_info in self.thumbnail_widgets:
            widget_info['frame'].configure(relief=tk.RAISED)
        
        # Set background color of selected item
        if 0 <= index < len(self.thumbnail_widgets):
            self.thumbnail_widgets[index]['frame'].configure(relief=tk.SUNKEN)
            self.current_selection = index
            
            # Call the callback if provided
            if self.on_select_callback:
                self.on_select_callback(index)

    def clear_list(self):
        """Clear all thumbnails from the list"""
        for widget_info in self.thumbnail_widgets:
            widget_info['frame'].destroy()
        
        self.thumbnail_widgets.clear()
        self.thumbnail_images.clear()
        self.image_paths.clear()
        self.current_selection = -1
        
        # Update scroll region
        self.frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def get_selected_path(self):
        """Get the path of the currently selected thumbnail"""
        if 0 <= self.current_selection < len(self.image_paths):
            return self.image_paths[self.current_selection]
        return None

    def get_selected_index(self):
        """Get the index of the currently selected thumbnail"""
        return self.current_selection

    def get_all_paths(self):
        """Get all image paths in the list"""
        return self.image_paths.copy()