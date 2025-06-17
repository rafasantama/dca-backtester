import os
import logging
from dotenv import load_dotenv
from dca_backtester.ai_analysis import BacktestAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ai_analysis():
    # Load environment variables
    load_dotenv()
    
    # Verify API keys are present
    openai_key = os.getenv('OPENAI_API_KEY')
    cryptocompare_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    
    if not openai_key:
        logger.error("OpenAI API key not found in environment variables")
        return
    if not cryptocompare_key:
        logger.error("CryptoCompare API key not found in environment variables")
        return
    
    logger.info("Successfully loaded API keys from environment variables")
    
    # Sample backtest results for testing
    sample_results = {
        'strategy_name': 'BTC DCA Weekly',
        'timeframe': '2023-01-01 to 2024-01-01',
        'total_investment': 10000,
        'final_value': 12500,
        'roi': 25.0,
        'apy': 22.5,
        'max_drawdown': 15.0,
        'volatility': 12.5,
        'sharpe_ratio': 1.8
    }
    
    try:
        # Initialize analyzer
        analyzer = BacktestAnalyzer()
        logger.info("Successfully initialized BacktestAnalyzer")
        
        # Get analysis
        analysis = analyzer.analyze_results(sample_results)
        logger.info("Successfully received analysis from OpenAI API")
        
        # Print results
        print("\n=== AI Analysis Results ===")
        print(analysis)
        print("==========================\n")
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    test_ai_analysis() 