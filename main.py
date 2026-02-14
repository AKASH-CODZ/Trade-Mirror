#!/usr/bin/env python3
"""
TradeMirror - Production Entry Point
Main application launcher with organized project structure
"""

import sys
import os
from pathlib import Path

# Add production modules to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "prod" / "core"))
sys.path.insert(0, str(project_root / "prod" / "ui"))
sys.path.insert(0, str(project_root / "prod" / "services"))

def main():
    """Launch the TradeMirror application"""
    try:
        # Import production modules
        from app import main as app_main
        
        print("🛡️  TradeMirror - Secure Trading Analytics")
        print("=" * 50)
        print("Launching production application...")
        
        # Run the main application
        app_main()
        
    except ImportError as e:
        print(f"❌ Failed to import required modules: {e}")
        print("Ensure all production dependencies are installed.")
        return 1
    except Exception as e:
        print(f"❌ Application error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)