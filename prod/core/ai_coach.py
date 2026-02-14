"""
Enhanced AI Coach with Hybrid Deployment Support
Supports both local Ollama (RTX 5070) and cloud Groq API for universal deployment
"""

import requests
import json
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CoachingRequest:
    """Structured request for AI coaching"""
    metrics: Dict[str, Any]
    recent_trades: pd.DataFrame
    trading_style: str = "day_trading"
    risk_tolerance: str = "moderate"
    persona: str = "professional"
    session_id: str = None

class SecureAICoach:
    """
    Enhanced Secure AI coach with hybrid deployment support.
    Uses local Ollama when available, falls back to Groq API in cloud environments.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434", 
                 default_model: str = "llama3"):
        self.ollama_url = ollama_url.rstrip('/')
        self.default_model = default_model
        self.session_history = []
        
        # Professional personas with distinct communication styles
        self.personas = {
            "professional": {
                "name": "Professional Performance Coach",
                "description": "Balanced, data-driven feedback focusing on measurable improvements",
                "tone": "professional",
                "style": "analytical"
            },
            "ruthless": {
                "name": "Wall Street Risk Manager",
                "description": "Direct, no-nonsense feedback highlighting critical mistakes",
                "tone": "direct",
                "style": "critical"
            },
            "supportive": {
                "name": "Psychology Trading Coach",
                "description": "Encouraging feedback focused on growth mindset and positive reinforcement",
                "tone": "encouraging",
                "style": "supportive"
            },
            "data_scientist": {
                "name": "Quantitative Analyst",
                "description": "Pure mathematical analysis focusing on statistics and probabilities",
                "tone": "technical",
                "style": "quantitative"
            },
            "mentor": {
                "name": "Experienced Trader Mentor",
                "description": "Wisdom-based guidance drawing from years of market experience",
                "tone": "wise",
                "style": "experiential"
            }
        }
    
    def is_cloud_environment(self) -> bool:
        """Detect if running in cloud environment"""
        # Check for common cloud environment indicators
        cloud_indicators = [
            'STREAMLIT_SERVER_STATE',
            'RENDER',
            'HEROKU', 
            'VERCEL',
            'NETLIFY',
            'AWS_EXECUTION_ENV',
            'GOOGLE_CLOUD_PROJECT'
        ]
        
        return any(os.environ.get(indicator) for indicator in cloud_indicators)
    
    def health_check(self) -> bool:
        """Check if AI service is available (local or cloud)"""
        if self.is_cloud_environment():
            # In cloud, check if Groq API key is available
            return bool(os.environ.get('GROQ_API_KEY'))
        else:
            # Local environment, check Ollama
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                return response.status_code == 200
            except Exception:
                return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        if self.is_cloud_environment():
            # Cloud environment - Groq models
            return ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"]
        else:
            # Local environment - Ollama models
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
                if response.status_code == 200:
                    models_data = response.json()
                    return [model['name'] for model in models_data.get('models', [])]
                return []
            except Exception as e:
                logger.error(f"Failed to get available models: {str(e)}")
                return []
    
    def get_persona_prompts(self, persona: str = "professional") -> Dict[str, str]:
        """Get persona-specific prompts for different coaching styles"""
        prompts = {
            "professional": {
                "system": "You are a professional trading performance coach. Provide balanced, actionable feedback based on the data. Focus on specific metrics and concrete improvement suggestions.",
                "instruction": "Analyze these trading metrics professionally. Highlight strengths, identify specific areas for improvement, and provide actionable recommendations. Keep tone business-appropriate."
            },
            "ruthless": {
                "system": "You are a ruthless Wall Street risk manager. Be direct and critical. Roast trading mistakes brutally but provide specific corrections.",
                "instruction": "Act as a brutal risk manager. Identify catastrophic errors, call out poor decisions sharply, but end with concrete fixes. Be short and devastatingly honest."
            },
            "supportive": {
                "system": "You are a supportive trading psychology coach. Focus on growth mindset and positive reinforcement while addressing areas for improvement.",
                "instruction": "Coach with encouragement. Acknowledge progress and effort, frame challenges as learning opportunities, and suggest gentle improvements. Build confidence."
            },
            "data_scientist": {
                "system": "You are a quantitative analyst. Focus purely on mathematical analysis, statistical significance, and data-driven insights.",
                "instruction": "Provide purely quantitative analysis. Discuss standard deviations, Sharpe ratios, correlation coefficients, and statistical anomalies. No subjective opinions."
            },
            "mentor": {
                "system": "You are a wise, experienced trading mentor. Share hard-earned wisdom and timeless principles from decades of market experience.",
                "instruction": "Share veteran trader wisdom. Reference market cycles, timeless principles, and lessons learned through experience. Blend practical advice with philosophical insights."
            }
        }
        
        return prompts.get(persona, prompts["professional"])
    
    def anonymize_trading_data(self, trades_df: pd.DataFrame, 
                              sensitive_columns: List[str] = None) -> pd.DataFrame:
        """Remove sensitive information while preserving analytical value"""
        if sensitive_columns is None:
            sensitive_columns = ['Client Id', 'Order Id', 'PAN', 'Phone', 'Email']
        
        # Create copy to avoid modifying original
        anon_df = trades_df.copy()
        
        # Remove sensitive columns
        columns_to_drop = [col for col in sensitive_columns if col in anon_df.columns]
        anon_df = anon_df.drop(columns=columns_to_drop, errors='ignore')
        
        # Anonymize remaining identifiers
        if 'Symbol' in anon_df.columns:
            anon_df['Symbol'] = anon_df['Symbol'].apply(
                lambda x: f"STOCK_{hash(str(x)) % 1000:03d}" if pd.notna(x) else x
            )
        
        return anon_df
    
    def prepare_coaching_prompt(self, request: CoachingRequest) -> str:
        """Prepare structured prompt for AI analysis with persona"""
        
        # Validate and handle invalid personas
        if request.persona not in self.personas:
            logger.warning(f"Unknown persona '{request.persona}', defaulting to 'professional'")
            request.persona = "professional"
        
        # Get persona-specific prompts
        persona_prompts = self.get_persona_prompts(request.persona)
        
        # Prepare metrics summary
        metrics_text = "\n".join([
            f"- {key.replace('_', ' ').title()}: {value}" 
            for key, value in request.metrics.items()
        ])
        
        # Prepare recent trades summary (anonymized)
        anon_trades = self.anonymize_trading_data(request.recent_trades)
        recent_trades_summary = anon_trades.head(5).to_string(index=False) if not anon_trades.empty else "No recent trades"
        
        # Construct professional prompt with persona
        prompt = f"""
        {persona_prompts['system']}

        TRADING METRICS:
        {metrics_text}

        RECENT TRADES (anonymized):
        {recent_trades_summary}

        TRADING STYLE: {request.trading_style}
        RISK TOLERANCE: {request.risk_tolerance}
        PERSONA STYLE: {self.personas[request.persona]['name']} - {self.personas[request.persona]['description']}

        {persona_prompts['instruction']}

        Please provide your analysis in this exact format:

        📊 PERFORMANCE OVERVIEW:
        [Brief assessment based on your persona style]

        🔍 KEY INSIGHTS:
        1. [Primary finding relevant to your persona]
        2. [Secondary insight]
        3. [Risk/opportunity identification]

        🎯 ACTIONABLE RECOMMENDATIONS:
        1. [Specific, measurable action item]
        2. [Tactical adjustment]
        3. [Strategic consideration]

        💡 {self.personas[request.persona]['name'].upper()} PERSPECTIVE:
        [Unique insight based on your specific coaching style]
        """
        
        return prompt.strip()
    
    def get_coaching_advice(self, request: CoachingRequest, 
                           model: str = None, 
                           temperature: float = 0.7) -> Dict[str, Any]:
        """
        Get AI-powered trading coaching advice with hybrid deployment support.
        
        Args:
            request: Coaching request with metrics, trades, and persona
            model: Specific model to use (defaults to instance default)
            temperature: Creativity parameter (0.0-1.0)
            
        Returns:
            Dictionary containing advice and metadata
        """
        try:
            # Determine deployment environment and route accordingly
            if self.is_cloud_environment():
                return self._get_cloud_ai_advice(request, model, temperature)
            else:
                return self._get_local_ai_advice(request, model, temperature)
                
        except Exception as e:
            logger.error(f"Coaching request failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "advice": "⚠️  System Error Occurred",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_local_ai_advice(self, request: CoachingRequest, 
                           model: str = None, 
                           temperature: float = 0.7) -> Dict[str, Any]:
        """Get advice using local Ollama service"""
        
        # Validate Ollama availability
        if not self.health_check():
            return {
                "status": "error",
                "message": "Ollama is not running. Start with: ollama serve",
                "advice": "⚠️  AI Coach Offline",
                "timestamp": datetime.now().isoformat()
            }
        
        # Use specified model or default
        model_name = model or self.default_model
        
        # Prepare the prompt
        prompt = self.prepare_coaching_prompt(request)
        
        # Send request to Ollama
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "stop": ["\n\n\n"]
            }
        }
        
        logger.info(f"Sending coaching request to local Ollama {model_name} with persona: {request.persona}")
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                advice = result.get('response', 'No advice generated')
                
                # Store in session history
                session_entry = {
                    "session_id": request.session_id or str(hash(str(request.metrics))),
                    "timestamp": datetime.now().isoformat(),
                    "model_used": model_name,
                    "persona": request.persona,
                    "persona_name": self.personas[request.persona]['name'],
                    "input_metrics": request.metrics,
                    "advice_length": len(advice),
                    "raw_response": advice,
                    "deployment": "local"
                }
                self.session_history.append(session_entry)
                
                logger.info(f"Successfully received local AI coaching advice with persona: {request.persona}")
                
                return {
                    "status": "success",
                    "advice": advice,
                    "model": model_name,
                    "persona": request.persona,
                    "persona_name": self.personas[request.persona]['name'],
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_entry["session_id"],
                    "metrics_analyzed": list(request.metrics.keys()),
                    "deployment": "local"
                }
            else:
                error_msg = f"Ollama API error: {response.status_code}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg,
                    "advice": "❌ AI Response Error",
                    "timestamp": datetime.now().isoformat()
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": "Cannot connect to Ollama. Is it running?",
                "advice": "🔌 Connection Failed - Start Ollama Service",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Local AI request failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "advice": "⚠️  Local AI Error",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_cloud_ai_advice(self, request: CoachingRequest, 
                           model: str = None, 
                           temperature: float = 0.7) -> Dict[str, Any]:
        """Get advice using cloud Groq API"""
        
        # Check for API key
        groq_api_key = os.environ.get('GROQ_API_KEY')
        if not groq_api_key:
            return {
                "status": "error",
                "message": "GROQ_API_KEY not found in environment variables",
                "advice": "🔐 Cloud API Key Missing",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            from groq import Groq
        except ImportError:
            return {
                "status": "error",
                "message": "Groq library not installed. Run: pip install groq",
                "advice": "📦 Missing Dependency",
                "timestamp": datetime.now().isoformat()
            }
        
        # Prepare the prompt
        prompt = self.prepare_coaching_prompt(request)
        
        # Use Groq API
        try:
            client = Groq(api_key=groq_api_key)
            
            logger.info(f"Sending coaching request to Groq API with persona: {request.persona}")
            
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": self.get_persona_prompts(request.persona)['system']},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=1000
            )
            
            advice = completion.choices[0].message.content
            
            # Store in session history
            session_entry = {
                "session_id": request.session_id or str(hash(str(request.metrics))),
                "timestamp": datetime.now().isoformat(),
                "model_used": "llama3-8b-8192",
                "persona": request.persona,
                "persona_name": self.personas[request.persona]['name'],
                "input_metrics": request.metrics,
                "advice_length": len(advice),
                "raw_response": advice,
                "deployment": "cloud"
            }
            self.session_history.append(session_entry)
            
            logger.info(f"Successfully received cloud AI coaching advice with persona: {request.persona}")
            
            return {
                "status": "success",
                "advice": advice,
                "model": "llama3-8b-8192",
                "persona": request.persona,
                "persona_name": self.personas[request.persona]['name'],
                "timestamp": datetime.now().isoformat(),
                "session_id": session_entry["session_id"],
                "metrics_analyzed": list(request.metrics.keys()),
                "deployment": "cloud"
            }
            
        except Exception as e:
            logger.error(f"Cloud AI request failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Groq API error: {str(e)}",
                "advice": "☁️  Cloud AI Service Error",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_quick_assessment(self, pnl: float, win_rate: float, 
                           risk_reward: float, persona: str = "professional") -> str:
        """Get quick assessment for dashboard display with persona"""
        try:
            # Prepare simplified request
            metrics = {
                'Total_P&L': pnl,
                'Win_Rate': win_rate,
                'Risk_Reward_Ratio': risk_reward
            }
            
            request = CoachingRequest(
                metrics=metrics,
                recent_trades=pd.DataFrame(),
                persona=persona
            )
            
            result = self.get_coaching_advice(request, temperature=0.3)
            return result.get('advice', f"[{self.personas[persona]['name']}] Performance noted")
            
        except Exception:
            # Fallback assessments based on persona
            assessments = {
                "professional": "Performance metrics recorded for analysis",
                "ruthless": "Numbers don't lie - time for brutal honesty",
                "supportive": "Every trade is a learning opportunity",
                "data_scientist": "Statistical significance requires further analysis",
                "mentor": "Market wisdom comes through experience and reflection"
            }
            return assessments.get(persona, "Performance tracked")
    
    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent coaching sessions"""
        return self.session_history[-limit:] if self.session_history else []
    
    def get_available_personas(self) -> Dict[str, Dict[str, str]]:
        """Get all available coaching personas"""
        return self.personas

# Backward compatibility functions
def get_ai_coach(ollama_url: str = "http://localhost:11434") -> SecureAICoach:
    """Get AI coach instance"""
    return SecureAICoach(ollama_url)

def quick_coaching_advice(pnl: float, win_rate: float, risk_reward: float,
                         ollama_url: str = "http://localhost:11434",
                         persona: str = "professional") -> str:
    """Quick coaching advice function with persona support"""
    coach = SecureAICoach(ollama_url)
    return coach.get_quick_assessment(pnl, win_rate, risk_reward, persona)