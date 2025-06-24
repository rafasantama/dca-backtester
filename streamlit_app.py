#!/usr/bin/env python3
"""
DCA Backtester - Main Launcher
Launch the DCA Strategy Tool with backtesting and live execution capabilities.
"""

import subprocess
import sys
import os

def main():
    """Launch the DCA Strategy Tool."""
    try:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path to the backtester app
        app_path = os.path.join(script_dir, "dca_backtester", "backtester_app.py")
        
        # Check if the app exists
        if not os.path.exists(app_path):
            print(f"❌ Error: App not found at {app_path}")
            return
        
        # Launch the app
        print("🚀 Launching DCA Strategy Tool...")
        print("📈 Features:")
        print("   • Strategy Configuration")
        print("   • Historical Backtesting")
        print("   • Live Execution (Mock)")
        print("   • Export/Import Strategies")
        print("   • Skip backtest option for direct live execution")
        print()
        
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error launching app: {e}")

if __name__ == "__main__":
    main() 