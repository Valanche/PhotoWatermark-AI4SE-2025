# PhotoWatermark-AI4SE Modular Structure

This application has been restructured into a modular architecture following Python best practices.

## Directory Structure

```
photowatermark/
├── __init__.py
├── main.py                 # Main entry point
├── requirements.txt        # Dependencies
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── dialogs.py          # Dialog utilities (CopyableMessageBox, etc.)
├── models/                 # Data models and image processing
│   ├── __init__.py
│   └── image_processor.py  # Image processing functions
├── views/                  # UI components
│   ├── __init__.py
│   ├── main_window.py      # Main application window
│   └── widgets/            # Custom widgets
│       ├── __init__.py
│       └── thumbnail_list.py
└── controllers/            # Application logic
    ├── __init__.py
    └── main_controller.py  # Main controller logic
```

## Module Descriptions

- `utils/dialogs.py`: Contains dialog-related utilities like the copyable error message box
- `models/image_processor.py`: Handles all image processing operations
- `views/main_window.py`: Contains the main GUI window implementation
- `views/widgets/thumbnail_list.py`: Custom widget for displaying image thumbnails
- `controllers/main_controller.py`: Coordinates between views and models

## Running the Application

The application can be run in two ways:

1. As a module (recommended):
   ```bash
   python -m photowatermark.main
   ```

2. Direct execution:
   ```bash
   python photowatermark/main.py
   ```

## Dependencies

- Pillow: For image processing
- tkinterdnd2: Optional, for drag-and-drop functionality