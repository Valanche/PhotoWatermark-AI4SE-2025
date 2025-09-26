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
    app = MainController()
    app.run()


if __name__ == "__main__":
    main()