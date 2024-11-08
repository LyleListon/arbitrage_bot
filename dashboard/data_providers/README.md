# Data Provider System

## Overview
The data provider system implements a flexible and extensible architecture for accessing market data, allowing seamless switching between simulated and live data sources. This is particularly useful for development, testing, and production environments.

## Architecture

### Base Provider (base_provider.py)
The abstract base class that defines the interface all data providers must implement:

```python
class BaseDataProvider(ABC):
    @abstractmethod
    def get_market_data(self) -> Dict[str, Union[float, str]]:
        """Get current market analysis data"""
        pass

    @abstractmethod
    def get_price_history(self, token: str) -> List[float]:
        """Get price history for a token"""
        pass

    @abstractmethod
    def get_liquidity_data(self) -> Dict[str, List[float]]:
        """Get liquidity depth data"""
        pass

    @abstractmethod
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        pass
```

### Simulated Provider (simulated_provider.py)
Provides realistic market data simulation:
- Generates price movements with trends and volatility
- Simulates market conditions and gas prices
- Uses random walk with drift for price simulation
- Implements realistic market patterns

Key Features:
```python
class SimulatedDataProvider(BaseDataProvider):
    def __init__(self):
        self.base_prices = {
            'ETH': 2000.0,
            'BTC': 35000.0,
            'USDC': 1.0,
            ...
        }
        self.volatility = {
            'ETH': 0.02,
            'BTC': 0.015,
            ...
        }
        self.trends = {...}  # Market trends
```

### Live Provider (live_provider.py)
Connects to real blockchain data sources:
- Uses Chainlink price feeds for accurate pricing
- Monitors actual network conditions
- Implements caching and rate limiting
- Handles network errors gracefully

Key Features:
```python
class LiveDataProvider(BaseDataProvider):
    def __init__(self, rpc_url: str, price_feeds: Dict[str, str]):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.price_feeds = {
            symbol: self.w3.eth.contract(
                address=address,
                abi=PRICE_FEED_ABI
            )
            for symbol, address in price_feeds.items()
        }
```

### Provider Factory (factory.py)
Manages provider instantiation:
- Creates appropriate provider based on configuration
- Handles provider dependencies
- Provides easy switching between data sources

Usage:
```python
from data_providers.factory import get_provider

# Get default provider (from environment)
provider = get_provider()

# Force specific provider
provider = get_provider(force_type='live')
```

## Data Structures

### Market Data
```python
{
    'volatility': float,      # Current market volatility (%)
    'trend': str,            # Market trend ('bullish', 'bearish', 'neutral')
    'opportunity_score': int, # Trading opportunity score (0-100)
    'gas_price': float,      # Current gas price in Gwei
    'gas_trend': str,        # Gas price trend ('rising', 'falling', 'stable')
    'network_congestion': str # Network status ('low', 'normal', 'high')
}
```

### Price History
```python
{
    'token': [
        float,  # Historical prices
        ...
    ]
}
```

### Liquidity Data
```python
{
    'depths': [
        float,  # Available liquidity at each level
        ...
    ],
    'slippage_levels': [
        float,  # Slippage percentages
        ...
    ]
}
```

### Network Stats
```python
{
    'gas_price': float,    # Current gas price in Gwei
    'base_fee': float,     # Base fee for EIP-1559
    'pending_transactions': int,  # Number of pending transactions
    'block_time': float,   # Average block time in seconds
    'network_congestion': str  # Network congestion level
}
```

## Configuration

### Environment Variables
```env
# Provider Selection
DATA_PROVIDER_TYPE=simulated  # or 'live'

# Live Provider Configuration
SEPOLIA_RPC_URL=your_rpc_url
```

### Price Feed Addresses (Sepolia)
```python
SEPOLIA_PRICE_FEEDS = {
    'ETH': '0x694AA1769357215DE4FAC081bf1f309aDC325306',
    'BTC': '0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43',
    'USDC': '0xA2F78ab2355fe2f984D808B5CeE7FD0A93D5270E',
    'DAI': '0x14866185B1962B63C3Ea9E03Bc1da838bab34C19',
    'LINK': '0xc59E3633BAAC79493d908e63626716e204A45EdF'
}
```

## Error Handling

### Simulated Provider
- Generates consistent data even with missing configuration
- Never throws exceptions during normal operation
- Provides fallback values for all data points

### Live Provider
```python
try:
    price = self._get_price(token)
    if price <= 0:
        logger.warning(f"Invalid price for {token}")
        return self._get_fallback_price(token)
except Exception as e:
    logger.error(f"Error getting price: {e}")
    return self._get_fallback_price(token)
```

## Best Practices

1. Provider Selection:
   - Use simulated provider for development/testing
   - Use live provider for production
   - Validate environment variables before using live provider

2. Data Handling:
   - Cache frequently accessed data
   - Implement rate limiting for external calls
   - Handle network errors gracefully
   - Provide fallback values

3. Provider Implementation:
   - Inherit from BaseDataProvider
   - Implement all abstract methods
   - Add comprehensive logging
   - Include error handling

4. Testing:
   ```python
   def test_provider():
       provider = get_provider('simulated')
       data = provider.get_market_data()
       assert 'volatility' in data
       assert 'trend' in data
       assert isinstance(data['opportunity_score'], int)
   ```

## Extensions

### Custom Provider Example
```python
class CustomProvider(BaseDataProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.initialize()

    def get_market_data(self) -> Dict[str, Union[float, str]]:
        # Custom implementation
        pass

    # Implement other required methods
```

### Provider Registration
```python
from .factory import DataProviderFactory

# Register custom provider
DataProviderFactory.register_provider('custom', CustomProvider)

# Use custom provider
provider = get_provider('custom')
```

## Dependencies
- `web3`: Ethereum interaction
- `python-dotenv`: Environment configuration
- Standard Python libraries (time, random, math, logging)

## Contributing
1. Follow the provider interface
2. Add comprehensive tests
3. Document all methods
4. Handle errors gracefully
5. Submit pull request
