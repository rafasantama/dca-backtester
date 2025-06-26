#!/usr/bin/env python3
"""
Entry point for the DCA Backtester Wizard with Automated Execution
"""

import sys
import os

# Debug print for environment variable
print("DEBUG: CRYPTOCOMPARE_API_KEY =", os.getenv("CRYPTOCOMPARE_API_KEY"))

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from dca_backtester.wizard_app import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative import...")
    
    # Alternative approach - import the module directly
    import dca_backtester.wizard_app as wizard_app
    
    if hasattr(wizard_app, 'main'):
        wizard_app.main()
    else:
        print("Could not find main function in wizard_app")
        print("Available functions:", [f for f in dir(wizard_app) if not f.startswith('_')]) 