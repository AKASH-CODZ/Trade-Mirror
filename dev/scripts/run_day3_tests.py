#!/usr/bin/env python3
"""
TradeMirror Day-3 - Comprehensive Test Runner
Tests visualization features, AI personas, and professional dashboard components
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

def run_visualization_verification():
    """Verify visualization components can be imported and instantiated"""
    print(f"\n{'='*60}")
    print("🎨 VISUALIZATION COMPONENT VERIFICATION")
    print(f"{'='*60}")
    
    try:
        # Add production modules to path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root / "prod" / "core"))
        
        from visuals import FinancialVisualizer, create_professional_dashboard
        from ai_coach import SecureAICoach
        
        # Test instantiation
        visualizer = FinancialVisualizer()
        ai_coach = SecureAICoach()
        
        print("✅ FinancialVisualizer instantiated successfully")
        print("✅ SecureAICoach instantiated successfully")
        print("✅ All visualization components imported correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Visualization verification failed: {str(e)}")
        return False

def run_sample_dashboard_test():
    """Test creating a sample dashboard with test data"""
    print(f"\n{'='*60}")
    print("📊 SAMPLE DASHBOARD GENERATION TEST")
    print(f"{'='*60}")
    
    try:
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # Add production modules to path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root / "prod" / "core"))
        
        from visuals import create_professional_dashboard
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        np.random.seed(42)
        
        sample_df = pd.DataFrame({
            'Date': dates,
            'Symbol': [f'STOCK_{i%5:02d}' for i in range(50)],
            'Realized P&L': np.random.normal(500, 1500, 50),
            'Quantity': np.random.randint(10, 100, 50),
            'Buy Value': np.random.uniform(5000, 20000, 50),
            'Sell Value': np.random.uniform(5200, 21000, 50)
        })
        sample_df['Win'] = sample_df['Realized P&L'] > 0
        sample_df['Trade_Count'] = 1
        
        # Create dashboard
        dashboard = create_professional_dashboard(sample_df)
        
        # Verify components
        required_components = ['equity_curve', 'weekday_heatmap', 
                             'monthly_performance', 'summary_stats']
        
        for component in required_components:
            assert component in dashboard, f"Missing component: {component}"
        
        print("✅ Dashboard created successfully")
        print(f"✅ Generated {len(dashboard['summary_stats'])} summary statistics")
        print("✅ All visualization components functional")
        
        return True
        
    except Exception as e:
        print(f"❌ Sample dashboard test failed: {str(e)}")
        return False

def main():
    """Main test runner"""
    print("📊 TradeMirror Day-3 - Professional Dashboard Testing Suite")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to project directory
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Test results storage
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'verifications': {},
        'summary': {}
    }
    
    # Run component verification
    all_results['verifications']['visualization'] = run_visualization_verification()
    all_results['verifications']['sample_dashboard'] = run_sample_dashboard_test()
    
    # Run test suites
    test_suites = [
        ('dev/tests/test_visuals_and_personas.py', 'Visualization & Persona Tests')
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
    verification_passed = sum(1 for v in all_results['verifications'].values() if v)
    total_verifications = len(all_results['verifications'])
    
    all_results['summary'] = {
        'total_test_suites': len(test_suites),
        'successful_suites': suite_successes,
        'total_tests': total_tests,
        'total_failures': total_failures,
        'total_errors': total_errors,
        'verifications_passed': verification_passed,
        'total_verifications': total_verifications,
        'overall_success': (
            suite_successes == len([t for t, _ in test_suites if Path(t).exists()]) and
            verification_passed == total_verifications
        )
    }
    
    # Print final summary
    print(f"\n{'='*60}")
    print("📊 DAY-3 TESTING SUMMARY")
    print(f"{'='*60}")
    print(f"Test Suites: {suite_successes}/{len([t for t, _ in test_suites if Path(t).exists()])} passed")
    print(f"Total Tests: {total_tests}")
    print(f"Failures: {total_failures}")
    print(f"Errors: {total_errors}")
    print(f"Component Verifications: {verification_passed}/{total_verifications} passed")
    print(f"Overall Status: {'🎉 SUCCESS' if all_results['summary']['overall_success'] else '💥 FAILED'}")
    
    # Save detailed results
    results_file = project_root / "day3_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n📝 Detailed results saved to: {results_file}")
    
    # Return appropriate exit code
    return 0 if all_results['summary']['overall_success'] else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)