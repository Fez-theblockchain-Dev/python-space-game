"""
Pygbag entry point - delegates to __main__.py.
Pygbag requires main.py in the app folder; this file runs game/__main__.py.
"""
import runpy
import os

# Resolve path to __main__.py (same directory as this file)
_main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "__main__.py")
runpy.run_path(_main_path, run_name="__main__")
