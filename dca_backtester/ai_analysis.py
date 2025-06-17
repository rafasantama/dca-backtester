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
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=self.api_key)
        logger.info("Successfully initialized OpenAI API key")

    def analyze_results(self, backtest_results: Dict[str, Any]) -> str:
        """
        Analyze backtesting results using OpenAI API and provide critical insights about risk, ROI, and APY.
        
        Args:
            backtest_results: Dictionary containing backtesting results with key metrics
            
        Returns:
            str: Critical analysis of the backtesting results
        """
        logger.info("Starting analysis of backtest results")
        
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

        logger.info(f"Analyzing strategy: {metrics['strategy_name']} for timeframe: {metrics['timeframe']}")

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
            logger.info("Sending request to OpenAI API")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a critical and transparent financial advisor. Your role is to provide honest, data-driven analysis and not sugar-coat the results. Compare everything to traditional financial benchmarks and be specific about risks and opportunities."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            logger.info("Successfully received response from OpenAI API")
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {str(e)}")
            return f"Error analyzing results: {str(e)}" 