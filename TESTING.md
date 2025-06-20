# Testing Documentation

This document describes the comprehensive testing infrastructure for the DCA Backtester with CDP AgentKit integration.

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── test_runner.py             # Comprehensive test runner utility
├── services/
│   ├── test_base_agent.py     # BaseAgentService and SpendTracker tests
│   └── test_wallet_manager.py # WalletManager and ExternalWalletConnector tests
├── ui/
│   └── test_live_execution.py # Live execution UI component tests
└── integration/
    └── test_agent_integration.py # End-to-end integration tests
```

## Running Tests

### Quick Start
```bash
# Run all tests
python3.11 -m pytest tests/ -v

# Run specific test categories
python3.11 -m pytest tests/services/ -v     # Service layer tests
python3.11 -m pytest tests/ui/ -v           # UI component tests
python3.11 -m pytest tests/integration/ -v # Integration tests
```

### Using the Test Runner
```bash
# Run all tests with the custom test runner
python tests/test_runner.py all

# Run specific test types
python tests/test_runner.py unit         # Service and UI tests
python tests/test_runner.py integration # Integration tests only
python tests/test_runner.py quick       # Fast test run with early exit

# With coverage reporting
python tests/test_runner.py all --coverage

# Check test dependencies
python tests/test_runner.py --check-deps
```

## Test Categories

### 1. Unit Tests

#### SpendTracker Tests (`test_base_agent.py`)
- Daily spending limit validation
- 24-hour rolling window tracking
- Spend recording and retrieval

#### BaseAgentService Tests (`test_base_agent.py`)
- Wallet connection validation
- DCA buy execution with limits
- Gas cost estimation and validation
- Network status reporting
- Error handling for all operations

#### WalletManager Tests (`test_wallet_manager.py`)
- CDP wallet creation and import
- Wallet balance retrieval
- Network verification
- Wallet management operations

#### ExternalWalletConnector Tests (`test_wallet_manager.py`)
- Web3 provider connection
- External wallet verification
- Gas price estimation
- Network information retrieval

#### UI Component Tests (`test_live_execution.py`)
- Network status display
- Wallet connection interface
- Manual execution components
- Error state handling

### 2. Integration Tests

#### Full Workflow Tests (`test_agent_integration.py`)
- Complete wallet connection flow
- Gas estimation across services
- Spend limit tracking across transactions
- Gas limit enforcement
- Network status integration
- Error propagation between services
- Balance checking across wallet types

## Mock Strategy

### CDP SDK Mocking
Since the CDP SDK requires actual API credentials and network access, all tests use comprehensive mocking:

```python
# Module-level mocking for CDP imports
with patch.dict('sys.modules', {
    'cdp': MagicMock(),
    'cdp.Cdp': MagicMock(),
    'cdp.Wallet': MagicMock(),
    'cdp.Asset': MagicMock()
}):
    # Import and test modules
```

### Service Mocking
Service dependencies are mocked at the interface level to test business logic without external dependencies.

### Network Mocking
All network calls (Web3, CoinGecko API) are mocked to ensure deterministic test results.

## Test Fixtures

### Shared Fixtures (`conftest.py`)
- `mock_settings`: Test configuration with safe defaults
- `mock_testnet_plan`: Sample DCA plan for testing
- `mock_transaction_receipt`: Sample transaction result
- `mock_agent_service`: Pre-configured service with mocks
- `mock_wallet_manager`: Mocked wallet management operations
- `mock_external_connector`: Mocked external connectivity
- `mock_requests_get`: Mocked HTTP requests
- `mock_cdp_wallet`: Mocked CDP wallet instance

## Test Coverage

The test suite covers:

- ✅ **Core Business Logic**: DCA execution, spend tracking, gas validation
- ✅ **Error Handling**: All exception types and error propagation
- ✅ **Integration Points**: Service-to-service communication
- ✅ **UI Components**: User interface validation and error states
- ✅ **Configuration**: Settings validation and environment handling
- ✅ **Network Operations**: Gas estimation, wallet verification, price feeds

## Continuous Integration

Tests are designed to run in CI environments with:
- No external dependencies
- Deterministic results
- Fast execution (< 30 seconds for full suite)
- Clear failure reporting

## Development Testing

### Running Tests During Development
```bash
# Watch mode (requires pytest-watch)
pip install pytest-watch
ptw tests/

# Run tests on file changes
python tests/test_runner.py quick

# Test specific functionality
python3.11 -m pytest tests/services/test_base_agent.py::TestSpendTracker -v
```

### Adding New Tests
1. Follow the existing pattern in the appropriate test directory
2. Use the shared fixtures from `conftest.py`
3. Mock external dependencies appropriately
4. Include both success and failure scenarios
5. Add integration tests for new service interactions

## Known Limitations

1. **CDP SDK**: Tests use mocks instead of real CDP integration
2. **Network Calls**: All external API calls are mocked
3. **UI Testing**: Streamlit components require additional mocking
4. **Async Testing**: Some async patterns may need pytest-asyncio configuration

## Future Enhancements

1. **E2E Testing**: Add end-to-end tests with testnet integration
2. **Performance Testing**: Add load tests for high-frequency operations
3. **Security Testing**: Add tests for credential handling and validation
4. **UI Integration**: Add Selenium-based UI tests for full interface testing