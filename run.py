#!/usr/bin/env python3
"""
Entry point for the AI Video Editor targeting DaVinci Resolve.
Run this file to start the full pipeline.
"""

import sys
import os
import traceback
from src.ui import launch_ui

def main():
    print("Launching GUI...")
    launch_ui()


if __name__ == "__main__":
    main()
