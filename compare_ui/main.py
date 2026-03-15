#!/usr/bin/env python3
"""
SubtitleCompare - VobSub/SRT Subtitle Comparison Tool

A GUI application for comparing VobSub (image-based) subtitles with SRT (text-based)
subtitles, allowing users to correct timing and text content.
"""

import sys
import os

# Add the compare_ui directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Change to the compare_ui directory so relative imports work
os.chdir(script_dir)

from ui.main_window import main

if __name__ == '__main__':
    main()
