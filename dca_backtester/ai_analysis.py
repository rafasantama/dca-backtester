import os
import logging
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class BacktestAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            logger.info("AI analysis will be disabled - consider setting OPENAI_API_KEY for enhanced insights")
        else:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("Successfully initialized OpenAI API key")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None

    def analyze_results(self, backtest_results: Dict[str, Any]) -> str:
        """
        Analyze backtesting results using OpenAI API and provide critical insights about risk, ROI, and APY.
        
        Args:
            backtest_results: Dictionary containing backtesting results with key metrics
            
        Returns:
            str: Critical analysis of the backtesting results
        """
        if not self.client:
            return self._generate_fallback_analysis(backtest_results)
            
        logger.info("🤖 Starting analysis of backtest results")
        
        # Extract relevant metrics
        metrics = {
            'strategy_name': backtest_results.get('strategy_name', 'Unknown'),
            'timeframe': backtest_results.get('timeframe', 'Unknown'),
            'total_investment': backtest_results.get('total_investment', 0),
            'final_value': backtest_results.get('final_value', 0),
            'roi': backtest_results.get('roi', 0),
            'apy': backtest_results.get('apy', 0),
            'volatility': backtest_results.get('volatility', 0),
            'sharpe_ratio': backtest_results.get('sharpe_ratio', 0),
            'number_of_trades': backtest_results.get('number_of_trades', 0),
            'dip_buys': backtest_results.get('dip_buys', 0),
            'peak_sells': backtest_results.get('peak_sells', 0),
            'avg_trade_size': backtest_results.get('avg_trade_size', 0)
        }

        logger.info(f"🔍 Analyzing strategy: {metrics['strategy_name']} for timeframe: {metrics['timeframe']}")

        # Create prompt for OpenAI with context about DCA backtester and traditional finance benchmarks
        prompt = f"""
        You are a critical and transparent financial advisor analyzing a cryptocurrency DCA strategy. 
        Be direct, honest, and compare results with traditional financial benchmarks.

        Current Market Context (2024):
        - High-yield savings accounts: 4-5% APY
        - S&P 500 average annual return: ~10-11%
        - US Treasury Bonds: 4-5% yield
        - Inflation rate: ~3-4%

        Strategy Details:
        - Regular investments at fixed intervals
        - Optional dip buying (increased investment during price drops)
        - Optional peak selling (profit taking during price increases)
        - Total investment: ${metrics['total_investment']:,.2f}
        - Final value: ${metrics['final_value']:,.2f}
        - Number of trades: {metrics['number_of_trades']}
        - Average trade size: ${metrics['avg_trade_size']:.2f}
        - Dip buys executed: {metrics['dip_buys']}
        - Peak sells executed: {metrics['peak_sells']}

        Performance Metrics:
        - ROI: {metrics['roi']:.2f}%
        - APY: {metrics['apy']:.2f}%
        - Volatility: {metrics['volatility']:.2f}%
        - Sharpe Ratio: {metrics['sharpe_ratio']:.2f}

        Please provide a critical analysis addressing:

        1. Performance vs Traditional Investments:
           - Compare APY ({metrics['apy']:.2f}%) with current market benchmarks
           - Is this return worth the risk compared to safer alternatives?
           - How does the ROI ({metrics['roi']:.2f}%) compare to traditional investment vehicles?
           - Be specific about opportunity costs and risk-adjusted returns

        2. Risk Assessment:
           - The volatility ({metrics['volatility']:.2f}%) is extremely high compared to traditional investments
           - Evaluate if the Sharpe ratio ({metrics['sharpe_ratio']:.2f}) justifies the risk
           - Analyze the effectiveness of risk management through dip buying and peak selling
           - Be honest about potential drawdowns and worst-case scenarios

        3. Strategy Critique and Recommendations:
           - Is the number of trades ({metrics['number_of_trades']}) optimal?
           - Are dip buys ({metrics['dip_buys']}) and peak sells ({metrics['peak_sells']}) being utilized effectively?
           - What specific changes would improve the strategy?
           - What are the red flags or concerns?

        Be direct and honest in your analysis. If the strategy underperforms traditional investments, say so. 
        If the risk is too high for the returns, point it out. Provide specific, actionable recommendations.
        """

        try:
            logger.info("�� Sending request to OpenAI API")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a critical and transparent financial advisor. Your role is to provide honest, data-driven analysis and not sugar-coat the results. Compare everything to traditional financial benchmarks and be specific about risks and opportunities."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            logger.info("✅ Successfully received response from OpenAI API")
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"🚨 Error in OpenAI API call: {str(e)}")
            return self._generate_fallback_analysis(backtest_results)
    
    def _generate_fallback_analysis(self, backtest_results: Dict[str, Any]) -> str:
        """Generate a basic analysis without OpenAI API."""
        try:
            metrics = {
                'roi': backtest_results.get('roi', 0),
                'apy': backtest_results.get('apy', 0),
                'volatility': backtest_results.get('volatility', 0),
                'sharpe_ratio': backtest_results.get('sharpe_ratio', 0),
                'total_investment': backtest_results.get('total_investment', 0),
                'final_value': backtest_results.get('final_value', 0),
                'number_of_trades': backtest_results.get('number_of_trades', 0),
                'dip_buys': backtest_results.get('dip_buys', 0),
                'peak_sells': backtest_results.get('peak_sells', 0)
            }
            
            analysis = []
            analysis.append("## 📊 Strategy Analysis (Basic Mode)")
            analysis.append("*Note: For enhanced AI-powered insights, set your OPENAI_API_KEY environment variable.*\n")
            
            # Performance vs benchmarks
            analysis.append("### 📈 Performance Summary")
            if metrics['roi'] > 0:
                analysis.append(f"✅ **Positive Return**: Your strategy generated a {metrics['roi']:.1f}% return (APY: {metrics['apy']:.1f}%)")
            else:
                analysis.append(f"❌ **Negative Return**: Your strategy resulted in a {abs(metrics['roi']):.1f}% loss (APY: {metrics['apy']:.1f}%)")
            
            # Benchmark comparisons
            analysis.append("\n### 🏦 Benchmark Comparison")
            if metrics['apy'] > 10:
                analysis.append(f"🎯 Your APY ({metrics['apy']:.1f}%) outperformed the S&P 500 average (~10-11%)")
            elif metrics['apy'] > 5:
                analysis.append(f"📊 Your APY ({metrics['apy']:.1f}%) exceeded high-yield savings rates (~4-5%)")
            elif metrics['apy'] > 0:
                analysis.append(f"⚠️ Your APY ({metrics['apy']:.1f}%) was positive but below traditional benchmarks")
            else:
                analysis.append(f"🚨 Your APY ({metrics['apy']:.1f}%) underperformed all traditional investments")
            
            # Risk assessment
            analysis.append("\n### ⚠️ Risk Assessment")
            if metrics['volatility'] > 50:
                analysis.append(f"🌊 **High Volatility**: {metrics['volatility']:.1f}% - Significantly higher than traditional investments")
            elif metrics['volatility'] > 30:
                analysis.append(f"📊 **Moderate Volatility**: {metrics['volatility']:.1f}% - Typical for crypto investments")
            else:
                analysis.append(f"🛡️ **Lower Volatility**: {metrics['volatility']:.1f}% - Relatively stable for crypto")
            
            if metrics['sharpe_ratio'] > 1:
                analysis.append(f"✅ **Good Risk-Adjusted Return**: Sharpe ratio of {metrics['sharpe_ratio']:.2f}")
            elif metrics['sharpe_ratio'] > 0:
                analysis.append(f"📊 **Moderate Risk-Adjusted Return**: Sharpe ratio of {metrics['sharpe_ratio']:.2f}")
            else:
                analysis.append(f"❌ **Poor Risk-Adjusted Return**: Sharpe ratio of {metrics['sharpe_ratio']:.2f}")
            
            # Strategy effectiveness
            analysis.append("\n### 🎯 Strategy Effectiveness")
            analysis.append(f"• **Total Trades**: {metrics['number_of_trades']}")
            analysis.append(f"• **Dip Buys**: {metrics['dip_buys']} (buying opportunities during price drops)")
            analysis.append(f"• **Peak Sells**: {metrics['peak_sells']} (profit-taking during price increases)")
            
            # Quick recommendations
            analysis.append("\n### 💡 Quick Recommendations")
            if metrics['roi'] < 0:
                analysis.append("• Consider adjusting your investment frequency or amounts")
                analysis.append("• Review the cryptocurrency selection - some assets may be more suitable for DCA")
                analysis.append("• Evaluate if dip buying thresholds need adjustment")
            elif metrics['volatility'] > 60:
                analysis.append("• Consider reducing position sizes to manage high volatility")
                analysis.append("• Implement more conservative risk management settings")
            elif metrics['sharpe_ratio'] < 0.5:
                analysis.append("• Focus on improving risk-adjusted returns")
                analysis.append("• Consider adjusting the strategy to reduce risk while maintaining returns")
            
            analysis.append("\n---")
            analysis.append("*💡 **Tip**: Set your OPENAI_API_KEY for detailed AI-powered analysis with specific recommendations and market context.*")
            
            return "\n".join(analysis)
            
        except Exception as e:
            logger.error(f"Error in fallback analysis: {e}")
            return "**Analysis Error**: Unable to generate analysis. Please check your backtest results and try again." 