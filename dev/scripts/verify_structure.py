#!/usr/bin/env python3
"""
Structure Verification Script
Validates that the organized project structure is working correctly
"""

import sys
import os
from pathlib import Path

def verify_production_structure():
    """Verify production code structure and imports"""
    print("🔍 Verifying Production Structure...")
    
    project_root = Path(__file__).parent.parent.parent
    prod_path = project_root / "prod"
    
    # Check required directories
    required_dirs = ["core", "ui", "services", "data"]
    for dir_name in required_dirs:
        dir_path = prod_path / dir_name
        if not dir_path.exists():
            print(f"❌ Missing production directory: {dir_path}")
            return False
        print(f"✅ Found: {dir_path}")
    
    # Check required files
    required_files = [
        "core/processor.py",
        "core/database.py", 
        "core/ai_coach.py",
        "ui/app.py",
        "requirements.txt"
    ]
    
    for file_path in required_files:
        full_path = prod_path / file_path
        if not full_path.exists():
            print(f"❌ Missing production file: {full_path}")
            return False
        print(f"✅ Found: {full_path}")
    
    return True

def verify_development_structure():
    """Verify development structure"""
    print("\n🔍 Verifying Development Structure...")
    
    project_root = Path(__file__).parent.parent.parent
    dev_path = project_root / "dev"
    
    # Check required dev directories
    required_dev_dirs = ["tests", "scripts", "verification", "temp"]
    for dir_name in required_dev_dirs:
        dir_path = dev_path / dir_name
        if not dir_path.exists():
            print(f"❌ Missing development directory: {dir_path}")
            return False
        print(f"✅ Found: {dir_path}")
    
    return True

def verify_imports():
    """Verify that production modules can be imported"""
    print("\n🔍 Verifying Module Imports...")
    
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root / "prod" / "core"))
    sys.path.insert(0, str(project_root / "prod" / "ui"))
    
    try:
        # Test core imports
        from processor import ZerodhaDataProcessor
        print("✅ processor module imported successfully")
        
        from database import SecureDatabase
        print("✅ database module imported successfully")
        
        from ai_coach import SecureAICoach
        print("✅ ai_coach module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main verification function"""
    print("🛡️  TradeMirror Structure Verification")
    print("=" * 50)
    
    # Verify structures
    prod_ok = verify_production_structure()
    dev_ok = verify_development_structure()
    imports_ok = verify_imports()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"Production Structure: {'✅ PASS' if prod_ok else '❌ FAIL'}")
    print(f"Development Structure: {'✅ PASS' if dev_ok else '❌ FAIL'}")
    print(f"Module Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    
    overall_success = prod_ok and dev_ok and imports_ok
    print(f"\nOverall Status: {'🎉 SUCCESS' if overall_success else '💥 FAILED'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)