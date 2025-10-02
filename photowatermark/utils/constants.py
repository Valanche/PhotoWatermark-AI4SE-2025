"""
PhotoWatermark-AI4SE constants module
"""

# 支持的图片格式
SUPPORTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')

# 默认配置
DEFAULT_WATERMARK_SIZE = 30
DEFAULT_WATERMARK_COLOR = (255, 255, 255)
DEFAULT_WATERMARK_TRANSPARENCY = 50
DEFAULT_WATERMARK_POSITION = 'bottom-right'
DEFAULT_QUALITY = 95

# UI 默认值
DEFAULT_WINDOW_SIZE = "1200x800"
THUMBNAIL_SIZE = (80, 80)

# 水印九宫格位置
WATERMARK_POSITIONS = [
    "top-left", "top-center", "top-right",
    "middle-left", "center", "middle-right",
    "bottom-left", "bottom-center", "bottom-right"
]

# 导出命名选项
NAMING_OPTIONS = ["保留原名", "添加前缀", "添加后缀"]

# 导出格式选项
FORMAT_OPTIONS = ["原格式", "JPEG", "PNG"]

# 导出尺寸选项
RESIZE_OPTIONS = ["原图尺寸", "按比例缩放", "指定宽度", "指定高度"]