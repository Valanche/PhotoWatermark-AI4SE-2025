"""
Main entry point for the PhotoWatermark-AI4SE application.
"""
import sys
import os

# Add the project root directory to the Python path to handle direct execution
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from photowatermark.controllers.main_controller import MainController


def main():
    # Create the main window first
    from photowatermark.views.main_window import MainWindow
    main_window = MainWindow()
    
    # Pass the window reference to the controller
    app = MainController(view=main_window)
    # Set the controller in the window so it can call controller methods
    main_window.controller = app
    
    # Run the application
    app.run()


if __name__ == "__main__":
    main()