#!/usr/bin/env python3
"""
TradeMirror Day 2 - Comprehensive Test Runner
Runs security tests, integration tests, and performance benchmarks
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path

def run_test_suite(test_file: str, description: str) -> dict:
    """Run a specific test suite and return results"""
    print(f"\n{'='*60}")
    print(f"🚀 Running {description}")
    print(f"{'='*60}")
    
    try:
        # Run tests with coverage
        cmd = [
            sys.executable, "-m", "pytest", test_file,
            "-v", "--tb=short", "--disable-warnings"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse results
        success = result.returncode == 0
        output_lines = result.stdout.strip().split('\n')
        
        # Extract test counts
        test_count = 0
        failure_count = 0
        error_count = 0
        
        for line in output_lines:
            if 'passed' in line and '::' in line:
                test_count += 1
            elif 'failed' in line and '::' in line:
                test_count += 1
                failure_count += 1
            elif 'error' in line and '::' in line:
                test_count += 1
                error_count += 1
        
        return {
            'success': success,
            'test_count': test_count,
            'failures': failure_count,
            'errors': error_count,
            'output': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
    except Exception as e:
        return {
            'success': False,
            'test_count': 0,
            'failures': 0,
            'errors': 1,
            'output': '',
            'stderr': str(e),
            'return_code': -1
        }

def run_security_audit():
    """Run security-focused checks"""
    print(f"\n{'='*60}")
    print("🔒 SECURITY AUDIT")
    print(f"{'='*60}")
    
    security_issues = []
    
    # Check for hardcoded secrets
    project_files = ['*.py', 'integrations/*.py']
    for pattern in project_files:
        try:
            import glob
            files = glob.glob(pattern)
            for file_path in files:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Look for common secret patterns
                    suspicious_patterns = [
                        r'api[key|secret]', 
                        r'password\s*=', 
                        r'token\s*=', 
                        r'secret\s*=',
                        r'AWS_ACCESS_KEY',
                        r'private[key|token]'
                    ]
                    
                    import re
                    for pattern in suspicious_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            security_issues.append(f"Potential secret in {file_path}")
                            
        except Exception as e:
            security_issues.append(f"Could not scan {pattern}: {str(e)}")
    
    # Check file permissions
    sensitive_files = ['data/token.json', 'data/credentials.json', 'data/broker_config.json']
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            try:
                stat_result = os.stat(file_path)
                # Check if readable by others (Unix/Linux/Mac)
                if stat_result.st_mode & 0o077 != 0:
                    security_issues.append(f"File {file_path} has loose permissions")
            except Exception as e:
                security_issues.append(f"Could not check permissions for {file_path}: {str(e)}")
    
    if security_issues:
        print("⚠️  SECURITY ISSUES FOUND:")
        for issue in security_issues:
            print(f"  • {issue}")
        return False
    else:
        print("✅ No obvious security issues detected")
        return True

def run_import_verification():
    """Verify all modules can be imported without errors"""
    print(f"\n{'='*60}")
    print("🔧 MODULE IMPORT VERIFICATION")
    print(f"{'='*60}")
    
    modules_to_test = [
        'processor',
        'database',
        'ai_coach',
        'integrations.gmail_fetcher',
        'integrations.shoonya_bridge'
    ]
    
    import_errors = []
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            import_errors.append(f"{module}: {str(e)}")
            print(f"❌ {module} - {str(e)}")
        except Exception as e:
            import_errors.append(f"{module}: {str(e)}")
            print(f"⚠️  {module} - {str(e)}")
    
    return len(import_errors) == 0

def main():
    """Main test runner"""
    print("🛡️  TradeMirror Day 2 - Comprehensive Testing Suite")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Test results storage
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'security_audit': None,
        'import_verification': None,
        'summary': {}
    }
    
    # Run import verification first
    all_results['import_verification'] = run_import_verification()
    
    # Run security audit
    all_results['security_audit'] = run_security_audit()
    
    # Run test suites
    test_suites = [
        ('test_day2_security.py', 'Security Tests'),
        ('test_day2_integration.py', 'Integration Tests')
    ]
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    suite_successes = 0
    
    for test_file, description in test_suites:
        if Path(test_file).exists():
            result = run_test_suite(test_file, description)
            all_results['tests'][test_file] = result
            
            total_tests += result['test_count']
            total_failures += result['failures']
            total_errors += result['errors']
            
            if result['success']:
                suite_successes += 1
                print(f"✅ {description} - PASSED ({result['test_count']} tests)")
            else:
                print(f"❌ {description} - FAILED")
                if result['stderr']:
                    print(f"Error output:\n{result['stderr']}")
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    # Generate summary
    all_results['summary'] = {
        'total_test_suites': len(test_suites),
        'successful_suites': suite_successes,
        'total_tests': total_tests,
        'total_failures': total_failures,
        'total_errors': total_errors,
        'security_passed': all_results['security_audit'],
        'imports_passed': all_results['import_verification'],
        'overall_success': (
            suite_successes == len([t for t, _ in test_suites if Path(t).exists()]) and
            all_results['security_audit'] and
            all_results['import_verification']
        )
    }
    
    # Print final summary
    print(f"\n{'='*60}")
    print("📊 TEST EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"Test Suites: {suite_successes}/{len([t for t, _ in test_suites if Path(t).exists()])} passed")
    print(f"Total Tests: {total_tests}")
    print(f"Failures: {total_failures}")
    print(f"Errors: {total_errors}")
    print(f"Security Audit: {'✅ PASSED' if all_results['security_audit'] else '❌ FAILED'}")
    print(f"Import Verification: {'✅ PASSED' if all_results['import_verification'] else '❌ FAILED'}")
    print(f"Overall Status: {'🎉 SUCCESS' if all_results['summary']['overall_success'] else '💥 FAILED'}")
    
    # Save detailed results
    results_file = project_root / "day2_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n📝 Detailed results saved to: {results_file}")
    
    # Return appropriate exit code
    return 0 if all_results['summary']['overall_success'] else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)