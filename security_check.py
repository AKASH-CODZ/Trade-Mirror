#!/usr/bin/env python3
"""
🛡️ TradeMirror Security Verification Script
Checks for potential sensitive data that might be committed to Git
"""

import os
import sys
import subprocess
import re
from pathlib import Path

def check_git_status():
    """Check if we're in a git repository and get status"""
    try:
        result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            return True
        return False
    except FileNotFoundError:
        print("❌ Git not found. Please install git first.")
        return False

def get_tracked_files():
    """Get list of files currently tracked by Git"""
    try:
        result = subprocess.run(['git', 'ls-files'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        return []
    except Exception:
        return []

def scan_for_sensitive_patterns(file_path):
    """Scan file content for sensitive patterns"""
    sensitive_patterns = [
        r'[A-Z0-9]{20,}',  # Long alphanumeric strings (potential API keys)
        r'api[_-]?key',    # API key references
        r'secret',         # Secret references
        r'password',       # Password references
        r'token',          # Token references
        r'private',        # Private references
        r'\d{10,}',        # Long number sequences (potential IDs)
        r'[A-Z]{2}[A-Z0-9]{10,}',  # PAN-like patterns
        r'\d{3}-\d{3}-\d{4}',      # Phone number patterns
        r'\d{10}',         # 10-digit numbers (potential phone/PAN)
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        findings = []
        for pattern in sensitive_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                findings.append({
                    'pattern': pattern,
                    'line': line_num,
                    'match': match.group()
                })
        
        return findings
    except Exception:
        return []

def check_file_security(file_path):
    """Check individual file for security issues"""
    issues = []
    
    # Check file extensions that shouldn't contain sensitive data
    dangerous_extensions = ['.csv', '.xlsx', '.xls', '.db', '.sqlite', '.json']
    if any(file_path.endswith(ext) for ext in dangerous_extensions):
        if not any(allowed in file_path.lower() for allowed in 
                  ['sample', 'example', 'test', 'mock', 'template']):
            issues.append("Contains actual data file that should be ignored")
    
    # Check for sensitive content
    sensitive_findings = scan_for_sensitive_patterns(file_path)
    if sensitive_findings:
        issues.extend([f"Sensitive pattern found: {finding['match']} (line {finding['line']})" 
                      for finding in sensitive_findings])
    
    return issues

def main():
    """Main security verification function"""
    print("🛡️  TradeMirror Security Verification")
    print("=" * 50)
    
    # Check if we're in a git repo
    if not check_git_status():
        print("❌ Not in a Git repository")
        return False
    
    print("✅ Git repository detected")
    
    # Get tracked files
    tracked_files = get_tracked_files()
    print(f"📁 Found {len(tracked_files)} tracked files")
    
    # Security checks
    security_issues = []
    sensitive_files = []
    
    print("\n🔍 Scanning for security issues...")
    
    for file_path in tracked_files:
        if not file_path:  # Skip empty lines
            continue
            
        full_path = Path(file_path)
        if not full_path.exists():
            continue
            
        # Check file security
        issues = check_file_security(full_path)
        if issues:
            security_issues.append((file_path, issues))
            
        # Check for obviously sensitive filenames
        sensitive_indicators = [
            'credential', 'secret', 'token', 'private', 'key', 'password',
            'pan', 'aadhar', 'ssn', 'bank', 'account'
        ]
        
        if any(indicator in file_path.lower() for indicator in sensitive_indicators):
            sensitive_files.append(file_path)
    
    # Report findings
    print(f"\n📊 Security Scan Results:")
    print(f"⚠️  Files with potential issues: {len(security_issues)}")
    print(f"🚨 Potentially sensitive files: {len(sensitive_files)}")
    
    if security_issues:
        print(f"\n📋 Detailed Issues:")
        for file_path, issues in security_issues:
            print(f"\n📄 {file_path}:")
            for issue in issues:
                print(f"   • {issue}")
    
    if sensitive_files:
        print(f"\n🚨 Sensitive Files Found:")
        for file_path in sensitive_files:
            print(f"   • {file_path}")
    
    # Overall assessment
    if not security_issues and not sensitive_files:
        print(f"\n✅ Security verification PASSED")
        print("No obvious security issues detected")
        return True
    else:
        print(f"\n❌ Security verification FAILED")
        print("Please review the issues above and update .gitignore accordingly")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)