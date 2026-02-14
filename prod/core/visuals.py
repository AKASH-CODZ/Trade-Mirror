"""
Professional Financial Dashboard Visualizations
Enterprise-grade charts and analytics for trading performance
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FinancialVisualizer:
    """Professional financial dashboard visualizations"""
    
    def __init__(self):
        self.color_palette = {
            'profit': '#00ff00',
            'loss': '#ff0000', 
            'neutral': '#ffff00',
            'primary': '#1f77b4',
            'secondary': '#ff7f0e'
        }
    
    def plot_equity_curve(self, df: pd.DataFrame) -> go.Figure:
        """
        Create professional equity curve with drawdown visualization
        
        Args:
            df: Trading data with Date and Realized P&L columns
            
        Returns:
            Plotly figure with equity curve and drawdown
        """
        try:
            # Ensure proper data sorting and preparation
            if 'Date' not in df.columns:
                raise ValueError("DataFrame must contain 'Date' column")
            
            df_sorted = df.sort_values('Date').copy()
            df_sorted['Cumulative P&L'] = df_sorted['Realized P&L'].cumsum()
            
            # Calculate drawdown metrics
            df_sorted['Peak'] = df_sorted['Cumulative P&L'].cummax()
            df_sorted['Drawdown'] = df_sorted['Cumulative P&L'] - df_sorted['Peak']
            df_sorted['Drawdown %'] = (df_sorted['Drawdown'] / df_sorted['Peak']) * 100
            
            # Create subplots for equity and drawdown
            fig = go.Figure()
            
            # Main equity curve
            fig.add_trace(go.Scatter(
                x=df_sorted['Date'],
                y=df_sorted['Cumulative P&L'],
                mode='lines',
                name='Equity Curve',
                line=dict(color=self.color_palette['profit'], width=3),
                hovertemplate='<b>Date:</b> %{x}<br><b>Equity:</b> ₹%{y:,.2f}<extra></extra>'
            ))
            
            # Add peak line
            fig.add_trace(go.Scatter(
                x=df_sorted['Date'],
                y=df_sorted['Peak'],
                mode='lines',
                name='Peak Equity',
                line=dict(color='rgba(255, 255, 255, 0.3)', width=1, dash='dot'),
                hovertemplate='<b>Peak:</b> ₹%{y:,.2f}<extra></extra>'
            ))
            
            # Add drawdown area
            fig.add_trace(go.Scatter(
                x=df_sorted['Date'],
                y=df_sorted['Drawdown'],
                fill='tonexty',
                mode='none',
                name='Drawdown',
                fillcolor='rgba(255, 0, 0, 0.3)',
                hovertemplate='<b>Drawdown:</b> ₹%{y:,.2f} (%{text}%)<extra></extra>',
                text=[f"{dd:.2f}" for dd in df_sorted['Drawdown %']]
            ))
            
            # Calculate key metrics for title
            total_return = df_sorted['Cumulative P&L'].iloc[-1]
            max_drawdown = df_sorted['Drawdown'].min()
            max_drawdown_pct = df_sorted['Drawdown %'].min()
            
            fig.update_layout(
                title=f'Account Growth & Drawdown<br><sub>Total Return: ₹{total_return:,.2f} | Max Drawdown: ₹{max_drawdown:,.2f} ({max_drawdown_pct:.1f}%)</sub>',
                template='plotly_dark',
                height=600,
                showlegend=True,
                hovermode='x unified',
                xaxis_title='Date',
                yaxis_title='Amount (₹)',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating equity curve: {str(e)}")
            raise
    
    def plot_weekday_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """
        Create heatmap showing performance by day of week
        
        Args:
            df: Trading data with Date column
            
        Returns:
            Plotly figure with weekday performance heatmap
        """
        try:
            if 'Date' not in df.columns:
                raise ValueError("DataFrame must contain 'Date' column")
            
            # Extract day of week and group by performance
            df_copy = df.copy()
            df_copy['DayOfWeek'] = df_copy['Date'].dt.day_name()
            df_copy['DayNum'] = df_copy['Date'].dt.dayofweek
            
            # Group by day and calculate metrics
            daily_stats = df_copy.groupby(['DayOfWeek', 'DayNum']).agg({
                'Realized P&L': ['sum', 'count', 'mean'],
                'Win': 'sum'
            }).round(2)
            
            daily_stats.columns = ['Total_P&L', 'Trade_Count', 'Avg_P&L', 'Winning_Trades']
            daily_stats = daily_stats.reset_index()
            
            # Reorder days properly
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            daily_stats['DayOfWeek'] = pd.Categorical(daily_stats['DayOfWeek'], categories=day_order, ordered=True)
            daily_stats = daily_stats.sort_values('DayNum')
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=daily_stats['Total_P&L'],
                x=daily_stats['DayOfWeek'],
                y=['Performance'],
                colorscale='RdYlGn',
                zmid=0,
                text=[[f"₹{p:,.2f}<br>{int(c)} trades<br>Avg: ₹{a:,.2f}" 
                      for p, c, a in zip(daily_stats['Total_P&L'], 
                                       daily_stats['Trade_Count'], 
                                       daily_stats['Avg_P&L'])]],
                texttemplate="%{text}",
                hovertemplate='<b>%{x}</b><br>' +
                             'Total P&L: ₹%{z:,.2f}<br>' +
                             'Trades: %{text}<extra></extra>',
                showscale=True
            ))
            
            # Find best and worst days
            best_day = daily_stats.loc[daily_stats['Total_P&L'].idxmax(), 'DayOfWeek']
            worst_day = daily_stats.loc[daily_stats['Total_P&L'].idxmin(), 'DayOfWeek']
            
            fig.update_layout(
                title=f'Trading Performance by Day of Week<br><sub>Best: {best_day} | Worst: {worst_day}</sub>',
                template='plotly_dark',
                height=400,
                xaxis_title='Day of Week',
                yaxis_title='',
                yaxis={'visible': False, 'showticklabels': False}
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating weekday heatmap: {str(e)}")
            raise
    
    def plot_monthly_performance(self, df: pd.DataFrame) -> go.Figure:
        """
        Create monthly performance bar chart
        
        Args:
            df: Trading data with Date column
            
        Returns:
            Plotly figure with monthly performance
        """
        try:
            if 'Date' not in df.columns:
                raise ValueError("DataFrame must contain 'Date' column")
            
            # Group by month
            df_copy = df.copy()
            df_copy['YearMonth'] = df_copy['Date'].dt.to_period('M')
            monthly_perf = df_copy.groupby('YearMonth').agg({
                'Realized P&L': 'sum',
                'Trade_Count': 'sum'
            }).reset_index()
            
            monthly_perf['YearMonth'] = monthly_perf['YearMonth'].astype(str)
            
            # Color coding based on performance
            colors = ['red' if x < 0 else 'green' for x in monthly_perf['Realized P&L']]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=monthly_perf['YearMonth'],
                    y=monthly_perf['Realized P&L'],
                    marker_color=colors,
                    text=[f"₹{x:,.2f}" for x in monthly_perf['Realized P&L']],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>P&L: ₹%{y:,.2f}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title='Monthly Performance',
                template='plotly_dark',
                height=400,
                xaxis_title='Month',
                yaxis_title='P&L (₹)',
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating monthly performance chart: {str(e)}")
            raise
    
    def create_dashboard_summary(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Create comprehensive dashboard summary statistics
        
        Args:
            df: Trading data
            
        Returns:
            Dictionary with summary statistics and insights
        """
        try:
            summary = {}
            
            # Basic metrics
            summary['total_trades'] = len(df)
            summary['winning_trades'] = df['Win'].sum()
            summary['losing_trades'] = (~df['Win']).sum()
            summary['win_rate'] = (summary['winning_trades'] / summary['total_trades']) * 100
            
            # P&L metrics
            summary['total_pnl'] = df['Realized P&L'].sum()
            summary['avg_win'] = df[df['Win']]['Realized P&L'].mean() if summary['winning_trades'] > 0 else 0
            summary['avg_loss'] = df[~df['Win']]['Realized P&L'].mean() if summary['losing_trades'] > 0 else 0
            
            # Risk metrics
            summary['max_win'] = df['Realized P&L'].max()
            summary['max_loss'] = df['Realized P&L'].min()
            summary['profit_factor'] = abs(summary['avg_win'] / summary['avg_loss']) if summary['avg_loss'] != 0 else float('inf')
            
            # Time-based insights
            if 'Date' in df.columns:
                df_sorted = df.sort_values('Date')
                summary['first_trade'] = df_sorted['Date'].iloc[0]
                summary['last_trade'] = df_sorted['Date'].iloc[-1]
                
                # Best and worst performing days
                daily_perf = df.groupby(df['Date'].dt.date)['Realized P&L'].sum()
                summary['best_day'] = daily_perf.idxmax()
                summary['best_day_pnl'] = daily_perf.max()
                summary['worst_day'] = daily_perf.idxmin()
                summary['worst_day_pnl'] = daily_perf.min()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating dashboard summary: {str(e)}")
            raise

# Convenience functions for easy integration
def create_professional_dashboard(df: pd.DataFrame) -> Dict[str, go.Figure]:
    """
    Create complete professional dashboard with all charts
    
    Args:
        df: Trading data
        
    Returns:
        Dictionary containing all dashboard figures
    """
    visualizer = FinancialVisualizer()
    
    dashboard = {
        'equity_curve': visualizer.plot_equity_curve(df),
        'weekday_heatmap': visualizer.plot_weekday_heatmap(df),
        'monthly_performance': visualizer.plot_monthly_performance(df),
        'summary_stats': visualizer.create_dashboard_summary(df)
    }
    
    return dashboard