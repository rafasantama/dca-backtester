# CDP AgentKit Integration Plan (Enhanced)

## Complete CDP AgentKit Integration Plan

### Configuration Summary
- **Network:** Base Sepolia Testnet
- **Wallet:** Non-custodial (user-connected)
- **Integration:** Fully integrated Streamlit app
- **Scope:** Simple periodic DCA execution
- **Risk Limits:** $1000/day spending, 1% max gas fees (USD based)

---

## Phase 1: Environment & Dependencies (Enhanced)

### 1.1 Dependency Management
**Switch to Poetry/pyproject.toml for version locking:**
```toml
[tool.poetry.dependencies]
cdp-sdk = "~0.0.4"
web3 = "~6.15.0"
eth-account = "~0.8.0"
pydantic-settings = "^2.0.0"
tenacity = "^8.2.0"  # For retry logic

[tool.poetry.group.live.dependencies]
# Live execution extras
streamlit-components = "^1.0.0"  # Replace streamlit-js

[tool.poetry.group.test.dependencies]
pytest-asyncio = "^0.21.0"
hardhat-py = "^1.0.0"  # Local blockchain fork
```

### 1.2 Environment Configuration (Pydantic Settings)
```python
# dca_backtester/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class AgentKitSettings(BaseSettings):
    """Type-safe environment configuration"""
    
    # CDP API Keys (clearer naming)
    cdp_api_key_id: str  # Public API Key ID
    cdp_private_key: str  # Private key (secret)
    
    # Network Configuration
    base_sepolia_rpc_url: str = "https://sepolia.base.org"
    chain_id: int = 84532
    
    # Risk Management
    max_daily_spend_usd: float = 1000.0
    max_gas_percentage: float = 1.0  # Max gas as % of tx value
    spend_reset_hours: int = 24  # Rolling 24h window
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

---

## Phase 2: Code Architecture (Split & Enhanced)

### Phase 2a: Service Layer with Mocks

### 2.1 Enhanced Models with Validation
```python
from pydantic import BaseModel, Field, validator
from typing import Literal, Union

class TestnetDCAPlan(DCAPlan):
    """Testnet-specific DCA plan with validation"""
    wallet_address: Optional[str] = None
    target_token_address: str
    funding_token_address: str
    max_gas_percentage: float = Field(1.0, gt=0, le=5.0)
    daily_spend_limit: float = Field(1000.0, gt=0, le=10000.0)
    network: Literal["base-sepolia"] = "base-sepolia"
    
    @validator('max_gas_percentage')
    def validate_gas_percentage(cls, v):
        if not 0 < v <= 5.0:
            raise ValueError('Gas percentage must be between 0-5%')
        return v

class MainnetDCAPlan(DCAPlan):
    """Mainnet-specific plan (future use)"""
    network: Literal["base-mainnet"] = "base-mainnet"
    # More restrictive limits for mainnet

LiveDCAPlan = Union[TestnetDCAPlan, MainnetDCAPlan]
```

### 2.2 Fully Typed Base Agent Service
```python
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from dataclasses import dataclass

@dataclass
class TransactionReceipt:
    """Structured transaction result"""
    tx_hash: str
    status: str
    gas_used: int
    gas_cost_usd: float

class AgentError(Exception):
    """Base exception for agent operations"""
    pass

class BaseAgentService:
    """CDP AgentKit integration for Base Sepolia"""
    
    def __init__(self, settings: AgentKitSettings):
        self.settings = settings
        self.network = "base-sepolia"
        self.chain_id = 84532
        self.cdp_client = None
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
    async def connect_wallet(self, wallet_address: str) -> bool:
        """Verify wallet connection and network."""
        # Implementation with retry logic
        
    async def execute_dca_buy(
        self, 
        plan: TestnetDCAPlan, 
        amount_usd: float
    ) -> TransactionReceipt:
        """Submit a single DCA buy, respecting gas & spend limits."""
        # Implementation with full error handling
        
    async def check_balances(self, wallet_address: str) -> Dict[str, float]:
        """Get wallet balances for relevant tokens."""
        # Implementation
        
    async def estimate_gas_cost_usd(self, transaction: Dict[str, Any]) -> float:
        """Estimate gas cost in USD using live oracle."""
        # Convert ETH gas to USD, enforce 1% cap
        
    def validate_spending_limits(self, amount_usd: float) -> bool:
        """Check 24-hour rolling spend limit."""
        # Implementation with Redis/file-based counter
```

### Phase 2b: UI Integration with State Management

### 2.3 Streamlit State Management
```python
# dca_backtester/ui/state_manager.py
import streamlit as st
import json
from pathlib import Path

class WizardState:
    """Manage wizard state across sessions"""
    
    @staticmethod
    def save_state(key: str, data: dict):
        """Persist state to session_state and local JSON"""
        st.session_state[key] = data
        state_file = Path("wizard_state.json")
        if state_file.exists():
            existing = json.loads(state_file.read_text())
        else:
            existing = {}
        existing[key] = data
        state_file.write_text(json.dumps(existing))
        
    @staticmethod
    def load_state(key: str) -> Optional[dict]:
        """Load state from session_state or local JSON"""
        if key in st.session_state:
            return st.session_state[key]
        
        state_file = Path("wizard_state.json")
        if state_file.exists():
            data = json.loads(state_file.read_text())
            return data.get(key)
        return None
```

---

## Phase 3: Implementation Structure (Enhanced)

### 3.1 Enhanced File Organization
```
dca_backtester/
├── services/
│   ├── __init__.py
│   ├── base_agent.py          # CDP AgentKit integration
│   ├── wallet_manager.py      # Wallet connection logic
│   └── mocks.py              # Service mocks for testing
├── ui/
│   ├── __init__.py
│   ├── state_manager.py      # Session state management
│   └── live_execution.py     # Live execution components
├── models.py                 # Enhanced with validation
├── config.py                 # Pydantic settings
├── exceptions.py             # Custom exception classes
└── web_app.py               # Main Streamlit app
```

### 3.2 Enhanced Streamlit Interface Flow
1. **Existing Backtesting** (unchanged)
2. **New "Live Execution" Tab**
3. **Network Status Check** (RPC eth_chainId() verification)
4. **Wallet Connection Wizard** (with state persistence)
5. **DCA Plan Configuration** (with real-time validation)
6. **Risk Limits Dashboard** (24h spend tracking)
7. **Execute/Monitor Dashboard** (with retry/status)

---

## Phase 4: Setup Instructions (Enhanced)

### 4.1 CDP API Keys
1. Visit [Coinbase Developer Platform](https://portal.cdp.coinbase.com/)
2. Create new project
3. Generate API key pair:
   - **API Key ID** → `CDP_API_KEY_ID` in .env
   - **Private Key** → `CDP_PRIVATE_KEY` in .env

### 4.2 Base Sepolia Testnet Setup
1. Add Base Sepolia to wallet:
   - **Network Name:** Base Sepolia
   - **RPC URL:** https://sepolia.base.org
   - **Chain ID:** 84532
   - **Currency:** ETH
2. Get testnet tokens:
   - ETH from [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet)
   - Test USDC from relevant faucet

---

## Phase 5: Enhanced Risk Management

### 5.1 Dynamic Gas Fee Protection
```python
async def validate_gas_cost(self, tx_value_usd: float, estimated_gas_eth: float) -> bool:
    """Enforce 1% gas cap using live ETH/USD oracle"""
    eth_price_usd = await self.get_eth_price_usd()
    gas_cost_usd = estimated_gas_eth * eth_price_usd
    gas_percentage = (gas_cost_usd / tx_value_usd) * 100
    
    if gas_percentage > self.settings.max_gas_percentage:
        raise AgentError(f"Gas cost {gas_percentage:.2f}% exceeds {self.settings.max_gas_percentage}% limit")
    
    return True
```

### 5.2 Rolling 24-Hour Spend Tracking
```python
class SpendTracker:
    """Track spending in 24-hour rolling window"""
    
    def __init__(self, max_spend_usd: float):
        self.max_spend = max_spend_usd
        self.spend_log = []  # List of (timestamp, amount) tuples
        
    def can_spend(self, amount_usd: float) -> bool:
        """Check if spend is within 24h limit"""
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        
        # Remove old entries
        self.spend_log = [(ts, amt) for ts, amt in self.spend_log if ts > cutoff]
        
        # Calculate current 24h spend
        current_spend = sum(amt for _, amt in self.spend_log)
        
        return (current_spend + amount_usd) <= self.max_spend
```

---

## Phase 6: Testing & Validation (Comprehensive)

### 6.1 Test Infrastructure
```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
async def mock_base_agent():
    """Mock BaseAgentService for testing"""
    agent = AsyncMock(spec=BaseAgentService)
    agent.execute_dca_buy.return_value = TransactionReceipt(
        tx_hash="0x123...",
        status="success", 
        gas_used=21000,
        gas_cost_usd=2.50
    )
    return agent

@pytest.fixture
def hardhat_fork():
    """Local Base Sepolia fork for integration tests"""
    # Setup Hardhat fork of Base Sepolia
    pass
```

### 6.2 Test Scenarios
- **Unit Tests:** Model validation, spend tracking, gas calculations
- **Integration Tests:** End-to-end with Hardhat fork
- **UI Tests:** Streamlit wizard flow with mocked services
- **Performance Tests:** Gas estimation accuracy under load

### 6.3 CI/CD Pipeline
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          poetry install --with test
          poetry run pytest
          poetry run mypy dca_backtester/
          poetry run ruff check .
```

---

## Phase 7: Phased Delivery Strategy

### Phase 7.1: Foundation (Week 1)
- ✅ Pydantic settings & validation
- ✅ Service interfaces with mocks  
- ✅ Basic UI wizard with state management

### Phase 7.2: Core Integration (Week 2)
- ✅ Real CDP AgentKit integration
- ✅ Gas estimation & spend tracking
- ✅ Network verification & wallet connection

### Phase 7.3: Polish & Testing (Week 3)
- ✅ Comprehensive test suite
- ✅ Error handling & retry logic
- ✅ UI/UX refinements

---

**This enhanced plan addresses all identified weak spots with robust solutions for production-ready implementation.**