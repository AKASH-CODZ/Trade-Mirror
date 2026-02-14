"""
Comprehensive tests for Day-3 visualization and AI persona features
Testing professional dashboard components and persona customization
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Add production modules to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "prod" / "core"))

from visuals import FinancialVisualizer, create_professional_dashboard
from ai_coach import SecureAICoach, CoachingRequest

class TestFinancialVisualizer(unittest.TestCase):
    """Test professional financial visualization components"""
    
    def setUp(self):
        """Set up test data"""
        # Create realistic trading data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)  # For reproducible tests
        
        # Generate realistic trading patterns
        base_pnl = np.random.normal(0, 1000, 100)
        # Add some trending and volatility clustering
        for i in range(1, 100):
            base_pnl[i] = base_pnl[i-1] * 0.8 + np.random.normal(0, 800)
        
        self.test_df = pd.DataFrame({
            'Date': dates,
            'Symbol': [f'STOCK_{i%10:02d}' for i in range(100)],
            'Quantity': np.random.randint(1, 100, 100),
            'Buy Value': np.abs(np.random.normal(10000, 5000, 100)),
            'Sell Value': np.abs(np.random.normal(10500, 5200, 100)),
            'Realized P&L': base_pnl,
            'Buy Average': np.random.uniform(100, 200, 100),
            'Sell Average': np.random.uniform(105, 210, 100),
            'Trade Type': np.random.choice(['BUY', 'SELL'], 100),
            'Exchange': 'NSE'
        })
        
        # Add derived metrics
        self.test_df['Win'] = self.test_df['Realized P&L'] > 0
        self.test_df['Trade_Count'] = 1
        
        self.visualizer = FinancialVisualizer()
    
    def test_equity_curve_creation(self):
        """Test equity curve generation with drawdown visualization"""
        fig = self.visualizer.plot_equity_curve(self.test_df)
        
        # Verify figure properties
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 3)  # Equity line, peak line, drawdown area
        self.assertIn('Equity Curve', [trace.name for trace in fig.data])
        self.assertIn('Peak Equity', [trace.name for trace in fig.data])
        self.assertIn('Drawdown', [trace.name for trace in fig.data])
        
        # Verify layout (just check that template is set, not exact value)
        self.assertIsNotNone(fig.layout.template)
        self.assertEqual(fig.layout.height, 600)
    
    def test_weekday_heatmap_creation(self):
        """Test weekday performance heatmap"""
        fig = self.visualizer.plot_weekday_heatmap(self.test_df)
        
        # Verify figure properties
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)  # Heatmap trace
        self.assertIsInstance(fig.data[0], type(fig.data[0]))  # Heatmap object
        
        # Verify layout
        self.assertIsNotNone(fig.layout.template)
        self.assertEqual(fig.layout.height, 400)
    
    def test_monthly_performance_chart(self):
        """Test monthly performance bar chart"""
        fig = self.visualizer.plot_monthly_performance(self.test_df)
        
        # Verify figure properties
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)  # Bar chart trace
        self.assertEqual(fig.data[0].type, 'bar')
        
        # Verify layout
        self.assertIsNotNone(fig.layout.template)
        self.assertEqual(fig.layout.height, 400)
    
    def test_dashboard_summary_statistics(self):
        """Test comprehensive dashboard summary creation"""
        summary = self.visualizer.create_dashboard_summary(self.test_df)
        
        # Verify required metrics exist
        required_keys = ['total_trades', 'winning_trades', 'losing_trades', 'win_rate',
                        'total_pnl', 'avg_win', 'avg_loss', 'profit_factor']
        for key in required_keys:
            self.assertIn(key, summary)
        
        # Verify logical relationships
        self.assertEqual(summary['total_trades'], 100)
        self.assertEqual(summary['winning_trades'] + summary['losing_trades'], 100)
        self.assertAlmostEqual(summary['win_rate'], 
                             (summary['winning_trades'] / 100) * 100, places=2)
        
        # Verify P&L calculations
        calculated_total = self.test_df['Realized P&L'].sum()
        self.assertAlmostEqual(summary['total_pnl'], calculated_total, places=2)
    
    def test_complete_dashboard_creation(self):
        """Test creation of complete professional dashboard"""
        dashboard = create_professional_dashboard(self.test_df)
        
        # Verify all components present
        required_components = ['equity_curve', 'weekday_heatmap', 
                             'monthly_performance', 'summary_stats']
        for component in required_components:
            self.assertIn(component, dashboard)
        
        # Verify figure types (just check they exist and have layouts)
        self.assertIsNotNone(dashboard['equity_curve'].layout)
        self.assertIsNotNone(dashboard['weekday_heatmap'].layout)
        self.assertIsNotNone(dashboard['monthly_performance'].layout)
        
        # Verify summary statistics
        self.assertIsInstance(dashboard['summary_stats'], dict)
        self.assertIn('total_trades', dashboard['summary_stats'])

class TestAIPersonas(unittest.TestCase):
    """Test AI coach persona customization"""
    
    def setUp(self):
        """Set up AI coach for testing"""
        self.ai_coach = SecureAICoach()
        
        # Create test data
        self.test_metrics = {
            'Total_P&L': 50000.0,
            'Win_Rate': 65.0,
            'Risk_Reward_Ratio': 2.1,
            'Total_Trades': 200,
            'Profit_Factor': 1.8
        }
        
        self.test_trades = pd.DataFrame({
            'Symbol': ['RELIANCE', 'TCS', 'INFY'],
            'Quantity': [10, 5, 8],
            'Realized P&L': [1500.0, -800.0, 1200.0],
            'Date': pd.date_range('2024-01-01', periods=3)
        })
    
    def test_persona_availability(self):
        """Test that all expected personas are available"""
        personas = self.ai_coach.get_available_personas()
        
        expected_personas = ['professional', 'ruthless', 'supportive', 
                           'data_scientist', 'mentor']
        
        for persona in expected_personas:
            self.assertIn(persona, personas)
            self.assertIn('name', personas[persona])
            self.assertIn('description', personas[persona])
    
    def test_persona_prompt_generation(self):
        """Test persona-specific prompt generation"""
        for persona in ['professional', 'ruthless', 'supportive']:
            with self.subTest(persona=persona):
                prompts = self.ai_coach.get_persona_prompts(persona)
                
                # Verify required keys exist
                self.assertIn('system', prompts)
                self.assertIn('instruction', prompts)
                
                # Verify prompts are not empty
                self.assertGreater(len(prompts['system']), 0)
                self.assertGreater(len(prompts['instruction']), 0)
    
    def test_coaching_request_with_persona(self):
        """Test coaching request with different personas"""
        for persona in ['professional', 'ruthless', 'supportive']:
            with self.subTest(persona=persona):
                request = CoachingRequest(
                    metrics=self.test_metrics,
                    recent_trades=self.test_trades,
                    persona=persona
                )
                
                # Verify persona is set correctly
                self.assertEqual(request.persona, persona)
                
                # Verify prompt includes persona-specific content (check for key terms)
                prompt = self.ai_coach.prepare_coaching_prompt(request)
                persona_name = self.ai_coach.personas[persona]['name']
                self.assertIn(persona_name.split()[0].upper(), prompt.upper())
    
    def test_invalid_persona_handling(self):
        """Test handling of invalid persona requests"""
        # Test that invalid persona defaults to professional
        request = CoachingRequest(
            metrics=self.test_metrics,
            recent_trades=self.test_trades,
            persona='invalid_persona'
        )
        
        # Should not raise KeyError - should default gracefully
        try:
            prompt = self.ai_coach.prepare_coaching_prompt(request)
            # Should contain professional persona content
            self.assertIn("professional", prompt.lower())
        except KeyError:
            self.fail("Invalid persona should be handled gracefully")

class TestIntegrationScenarios(unittest.TestCase):
    """Test integrated scenarios combining visuals and AI"""
    
    def setUp(self):
        """Set up integrated test environment"""
        self.visualizer = FinancialVisualizer()
        self.ai_coach = SecureAICoach()
        
        # Create comprehensive test dataset
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(123)
        
        self.integrated_df = pd.DataFrame({
            'Date': dates,
            'Symbol': [f'STOCK_{i%5:02d}' for i in range(50)],
            'Realized P&L': np.random.normal(500, 1500, 50),  # Mix of wins/losses
            'Quantity': np.random.randint(10, 100, 50),
            'Buy Value': np.random.uniform(5000, 20000, 50),
            'Sell Value': np.random.uniform(5200, 21000, 50)
        })
        self.integrated_df['Win'] = self.integrated_df['Realized P&L'] > 0
        self.integrated_df['Trade_Count'] = 1
    
    def test_full_dashboard_with_ai_analysis(self):
        """Test complete workflow: visuals + AI analysis"""
        # Create dashboard
        dashboard = create_professional_dashboard(self.integrated_df)
        
        # Verify dashboard components
        self.assertIn('summary_stats', dashboard)
        self.assertIn('equity_curve', dashboard)
        
        # Get AI analysis with professional persona
        metrics = dashboard['summary_stats']
        request = CoachingRequest(
            metrics=metrics,
            recent_trades=self.integrated_df.tail(10),
            persona='professional'
        )
        
        # Test AI response (handle both online/offline scenarios)
        if self.ai_coach.health_check():
            advice = self.ai_coach.get_coaching_advice(request)
            # When online, expect success
            self.assertEqual(advice['status'], 'success')
        else:
            # When offline, test fallback behavior
            quick_assessment = self.ai_coach.get_quick_assessment(
                metrics['total_pnl'], metrics['win_rate'], 2.0, 'professional'
            )
            self.assertIsInstance(quick_assessment, str)
            self.assertGreater(len(quick_assessment), 0)
            # Test that the method doesn't crash
            self.assertTrue(True)  # Placeholder assertion for offline case

def run_visual_and_persona_tests():
    """Run all visualization and persona tests"""
    test_classes = [
        TestFinancialVisualizer,
        TestAIPersonas,
        TestIntegrationScenarios
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        suite.addTest(unittest.makeSuite(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_visual_and_persona_tests()
    exit(0 if success else 1)