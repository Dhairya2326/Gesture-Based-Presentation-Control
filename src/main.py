"""
Main Application Entry Point for Gesture-Based Presentation Control.
Milestone: Up to Week 4 (OpenCV Webcam Pipeline & Tkinter GUI).
"""

import sys
import argparse
import tkinter as tk

from src.gui.app import PresentationControllerApp


def parse_arguments():
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Gesture-Based Presentation Control (Milestone Week 4)"
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Webcam device index to use (default: 0)",
    )
    return parser.parse_args()


def main():
    """Application main function."""
    args = parse_arguments()

    print("=" * 60)
    print("  GESTURE-BASED PRESENTATION CONTROL")
    print("  Milestone: Week 4 (Tkinter GUI & OpenCV Video Pipeline)")
    print("  Team Members:")
    print("    1. Dhruv Pankhania (24001158)")
    print("    2. Krish Jadav     (24000638)")
    print("    3. Dhairya Patel   (24001142)")
    print("=" * 60)

    # Initialize Tkinter root window
    root = tk.Tk()

    # Launch GUI Application
    app = PresentationControllerApp(root, camera_index=args.camera_index)

    # Run main GUI event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nShutdown signal received. Exiting cleanly...")
        app.on_close()


if __name__ == "__main__":
    main()