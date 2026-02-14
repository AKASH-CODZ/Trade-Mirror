#!/usr/bin/env python3
"""
Comprehensive test runner for TradeMirror processor.
Runs all tests and generates detailed reports.
"""

import unittest
import sys
import os
from pathlib import Path
import coverage
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_tests_with_coverage():
    """Run tests with coverage analysis"""
    
    # Start coverage measurement
    cov = coverage.Coverage(
        source=['processor'],
        omit=['tests/*', '*/site-packages/*']
    )
    cov.start()
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    
    # Run tests with custom result handler
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Stop coverage measurement
    cov.stop()
    cov.save()
    
    # Generate coverage report
    print("\n" + "="*60)
    print("COVERAGE REPORT")
    print("="*60)
    cov.report()
    
    # Generate HTML coverage report
    cov.html_report(directory='coverage_html')
    print(f"\nDetailed HTML coverage report saved to: coverage_html/index.html")
    
    return result

def generate_test_report(result):
    """Generate detailed test report"""
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
        },
        'failures': [],
        'errors': []
    }
    
    # Process failures
    for test, traceback in result.failures:
        report['failures'].append({
            'test': str(test),
            'error': traceback
        })
    
    # Process errors
    for test, traceback in result.errors:
        report['errors'].append({
            'test': str(test),
            'error': traceback
        })
    
    # Save report
    with open('test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed test report saved to: test_report.json")
    return report

def print_summary(report):
    """Print test execution summary"""
    
    print("\n" + "="*60)
    print("TEST EXECUTION SUMMARY")
    print("="*60)
    print(f"Tests Run: {report['summary']['tests_run']}")
    print(f"Failures: {report['summary']['failures']}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Timestamp: {report['timestamp']}")
    
    if report['failures']:
        print("\nFAILURES:")
        for failure in report['failures']:
            print(f"  - {failure['test']}")
    
    if report['errors']:
        print("\nERRORS:")
        for error in report['errors']:
            print(f"  - {error['test']}")

def main():
    """Main test execution function"""
    
    print("🚀 Starting TradeMirror Comprehensive Tests")
    print("="*60)
    
    try:
        # Run tests with coverage
        result = run_tests_with_coverage()
        
        # Generate detailed report
        report = generate_test_report(result)
        
        # Print summary
        print_summary(report)
        
        # Return appropriate exit code
        if result.wasSuccessful():
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)