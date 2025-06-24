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
        
        IMPORTANT: Format your response with markdown headers, bullet points, and emojis to make it engaging and easy to read.
        Use relevant emojis throughout (📈, 📉, ⚠️, ✅, 🎯, 💰, 🚀, etc.) but don't overdo it.

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

        Please provide a critical analysis using markdown formatting with these sections:

        ## 📊 Performance vs Traditional Investments
        - Compare APY ({metrics['apy']:.2f}%) with current market benchmarks
        - Is this return worth the risk compared to safer alternatives?
        - How does the ROI ({metrics['roi']:.2f}%) compare to traditional investment vehicles?
        - Be specific about opportunity costs and risk-adjusted returns

        ## ⚠️ Risk Assessment  
        - The volatility ({metrics['volatility']:.2f}%) compared to traditional investments
        - Evaluate if the Sharpe ratio ({metrics['sharpe_ratio']:.2f}) justifies the risk
        - Analyze the effectiveness of risk management through dip buying and peak selling
        - Be honest about potential drawdowns and worst-case scenarios

        ## 🎯 Strategy Critique and Recommendations
        - Is the number of trades ({metrics['number_of_trades']}) optimal?
        - Are dip buys ({metrics['dip_buys']}) and peak sells ({metrics['peak_sells']}) being utilized effectively?
        - What specific changes would improve the strategy?
        - What are the red flags or concerns?

        Be direct and honest in your analysis. If the strategy underperforms traditional investments, say so. 
        If the risk is too high for the returns, point it out. Provide specific, actionable recommendations.
        Use emojis appropriately to make the analysis engaging and easy to scan.
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
            analysis.append("# 🤖 AI Strategy Analysis")
            analysis.append("*💡 For enhanced AI-powered insights, set your OPENAI_API_KEY environment variable.*")
            analysis.append("")
            
            # Performance vs benchmarks with enhanced emojis
            analysis.append("## 📈 Performance Summary")
            if metrics['roi'] > 0:
                if metrics['roi'] > 20:
                    analysis.append(f"🚀 **Excellent Return**: Your strategy generated an outstanding {metrics['roi']:.1f}% return!")
                    analysis.append(f"🎯 **Annual Performance**: {metrics['apy']:.1f}% APY - Well above market expectations")
                elif metrics['roi'] > 10:
                    analysis.append(f"✅ **Strong Return**: Your strategy generated a solid {metrics['roi']:.1f}% return")
                    analysis.append(f"📊 **Annual Performance**: {metrics['apy']:.1f}% APY - Good performance overall")
                else:
                    analysis.append(f"✅ **Positive Return**: Your strategy generated a {metrics['roi']:.1f}% return")
                    analysis.append(f"📈 **Annual Performance**: {metrics['apy']:.1f}% APY - Modest but positive gains")
            else:
                analysis.append(f"❌ **Negative Return**: Your strategy resulted in a {abs(metrics['roi']):.1f}% loss")
                analysis.append(f"📉 **Annual Performance**: {metrics['apy']:.1f}% APY - Strategy needs improvement")
            
            # Enhanced benchmark comparisons
            analysis.append("")
            analysis.append("## 🏆 Benchmark Comparison")
            
            if metrics['apy'] > 15:
                analysis.append(f"🥇 **Outstanding Performance**: Your {metrics['apy']:.1f}% APY crushes all traditional investments!")
                analysis.append("🎯 **vs S&P 500**: ~5% higher than historical average (10-11%)")
                analysis.append("💎 **vs High-Yield Savings**: ~10% higher than current rates (4-5%)")
            elif metrics['apy'] > 10:
                analysis.append(f"🥈 **Strong Performance**: Your {metrics['apy']:.1f}% APY outperformed the S&P 500!")
                analysis.append("📊 **vs S&P 500**: Competitive with historical average (10-11%)")
                analysis.append("🎯 **vs High-Yield Savings**: ~5-6% higher than current rates")
            elif metrics['apy'] > 5:
                analysis.append(f"🥉 **Decent Performance**: Your {metrics['apy']:.1f}% APY exceeded high-yield savings")
                analysis.append("⚠️ **vs S&P 500**: Below historical average, but still respectable")
                analysis.append("📈 **vs High-Yield Savings**: Higher than current rates (4-5%)")
            elif metrics['apy'] > 0:
                analysis.append(f"⚠️ **Below Benchmarks**: Your {metrics['apy']:.1f}% APY was positive but underwhelming")
                analysis.append("📉 **vs Traditional Investments**: Consider if crypto risk is worth it")
            else:
                analysis.append(f"🚨 **Underperformed**: Your {metrics['apy']:.1f}% APY lost to inflation and all alternatives")
                analysis.append("❌ **Strategy Review Needed**: Time to reconsider this approach")
            
            # Enhanced risk assessment
            analysis.append("")
            analysis.append("## ⚠️ Risk Assessment")
            
            if metrics['volatility'] > 60:
                analysis.append(f"🌪️ **Extreme Volatility**: {metrics['volatility']:.1f}% - This is a wild roller coaster ride!")
                analysis.append("🎢 **Risk Level**: Very High - Prepare for major price swings")
            elif metrics['volatility'] > 40:
                analysis.append(f"🌊 **High Volatility**: {metrics['volatility']:.1f}% - Significantly higher than traditional investments")
                analysis.append("⚡ **Risk Level**: High - Expect significant ups and downs")
            elif metrics['volatility'] > 20:
                analysis.append(f"📊 **Moderate Volatility**: {metrics['volatility']:.1f}% - Typical for crypto investments")
                analysis.append("🎯 **Risk Level**: Medium - Some bumps but manageable")
            else:
                analysis.append(f"🛡️ **Lower Volatility**: {metrics['volatility']:.1f}% - Surprisingly stable for crypto")
                analysis.append("✅ **Risk Level**: Relatively Low - Smoother ride than expected")
            
            # Risk-adjusted returns with emojis
            if metrics['sharpe_ratio'] > 1.5:
                analysis.append(f"💎 **Excellent Risk-Adjusted Returns**: Sharpe ratio of {metrics['sharpe_ratio']:.2f} - Great risk vs reward!")
            elif metrics['sharpe_ratio'] > 1:
                analysis.append(f"✅ **Good Risk-Adjusted Returns**: Sharpe ratio of {metrics['sharpe_ratio']:.2f} - Decent compensation for risk")
            elif metrics['sharpe_ratio'] > 0:
                analysis.append(f"📊 **Moderate Risk-Adjusted Returns**: Sharpe ratio of {metrics['sharpe_ratio']:.2f} - Could be better")
            else:
                analysis.append(f"❌ **Poor Risk-Adjusted Returns**: Sharpe ratio of {metrics['sharpe_ratio']:.2f} - Too much risk for the return")
            
            # Enhanced strategy effectiveness
            analysis.append("")
            analysis.append("## 🎯 Strategy Effectiveness")
            analysis.append(f"📊 **Trading Activity**: {metrics['number_of_trades']} total trades executed")
            
            if metrics['dip_buys'] > 0:
                analysis.append(f"📉 **Dip Buying**: {metrics['dip_buys']} opportunities captured - Smart buying during drops! 🎯")
            else:
                analysis.append("📉 **Dip Buying**: No dip buys executed - Consider enabling dip buying strategy")
                
            if metrics['peak_sells'] > 0:
                analysis.append(f"📈 **Peak Selling**: {metrics['peak_sells']} profit-taking trades - Good exit timing! 💰")
            else:
                analysis.append("📈 **Peak Selling**: No peak sells executed - Pure DCA approach")
            
            # Investment overview
            profit_loss = metrics['final_value'] - metrics['total_investment']
            if profit_loss > 0:
                analysis.append(f"💰 **Investment Journey**: ${metrics['total_investment']:,.0f} → ${metrics['final_value']:,.0f} (+${profit_loss:,.0f})")
            else:
                analysis.append(f"💸 **Investment Journey**: ${metrics['total_investment']:,.0f} → ${metrics['final_value']:,.0f} ({profit_loss:,.0f})")
            
            # Smart recommendations with emojis
            analysis.append("")
            analysis.append("## 💡 Smart Recommendations")
            
            if metrics['roi'] < 0:
                analysis.append("🔧 **Strategy Adjustments Needed:**")
                analysis.append("   • 📅 Consider changing investment frequency (weekly vs monthly)")
                analysis.append("   • 💰 Adjust investment amounts - smaller or larger positions")
                analysis.append("   • 🎯 Review asset selection - some cryptos work better for DCA")
                analysis.append("   • 📉 Fine-tune dip buying thresholds for better entry points")
            elif metrics['volatility'] > 60:
                analysis.append("🛡️ **Risk Management Focus:**")
                analysis.append("   • 📉 Reduce position sizes to manage extreme volatility")
                analysis.append("   • ⚖️ Implement more conservative risk management settings")
                analysis.append("   • 🎯 Consider taking profits more frequently during peaks")
            elif metrics['sharpe_ratio'] < 0.5:
                analysis.append("⚖️ **Risk-Return Optimization:**")
                analysis.append("   • 📊 Focus on improving risk-adjusted returns")
                analysis.append("   • 🛡️ Add more defensive elements to reduce downside risk")
                analysis.append("   • 🎯 Fine-tune entry and exit strategies")
            else:
                analysis.append("🎯 **Strategy is Working Well:**")
                analysis.append("   • ✅ Keep current approach - it's performing nicely")
                analysis.append("   • 📈 Consider gradually increasing position sizes")
                analysis.append("   • 🔍 Monitor for market changes that might require adjustments")
            
            analysis.append("")
            analysis.append("---")
            analysis.append("🚀 **Want More Detailed Analysis?**")
            analysis.append("Set your `OPENAI_API_KEY` environment variable for:")
            analysis.append("• 🤖 Advanced AI-powered insights and recommendations")
            analysis.append("• 📊 Detailed market context and comparisons")
            analysis.append("• 🎯 Personalized strategy optimization suggestions")
            analysis.append("• 📈 Risk assessment with specific actionable steps")
            
            return "\n".join(analysis)
            
        except Exception as e:
            logger.error(f"Error in fallback analysis: {e}")
            return "**Analysis Error**: Unable to generate analysis. Please check your backtest results and try again." 