"""
PhotoWatermark-AI4SE Package
"""
__version__ = "1.0.0"
__author__ = "AI4SE Team"

# 导入主要模块
from .models import *
from .views import *
from .controllers import *
from .utils import *

__all__ = [
    "__version__",
    "models",
    "views", 
    "controllers",
    "utils"
]