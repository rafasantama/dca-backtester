"""Main entry point for the Streamlit application."""
import sys
import os

# Get the absolute path to the venv's site-packages directory
# and add it to the system path. This is a robust way to ensure
# all installed packages are discoverable.
venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "lib", "python3.13", "site-packages")
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

from dca_backtester.web_app import app

if __name__ == "__main__":
    app() 