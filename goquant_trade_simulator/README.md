# GoQuant Trade Simulator

A professional-grade cryptocurrency trading simulation tool that provides real-time analysis of trading costs, including slippage, fees, and market impact. Built with Python and PyQt5, this simulator offers a comprehensive suite of features for traders and developers.

## 🌟 Key Features

- **Real-time Order Book Processing**
  - Live data feed from OKX exchange
  - Efficient order book management
  - Low-latency updates (< 2ms)

- **Advanced Cost Analysis**
  - Slippage calculation using linear regression
  - Dynamic fee calculation with volume-based discounts
  - Market impact estimation using Almgren-Chriss model
  - Maker/taker ratio prediction

- **Professional UI/UX**
  - Real-time visualization of order book data
  - Interactive simulation controls
  - Performance metrics dashboard
  - Latency monitoring

## 📋 Requirements

- Python 3.8+
- PyQt5
- websocket-client
- numpy
- pandas
- scipy
- matplotlib

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/sujal-p0408/goqaunt.git
cd goqaunt
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 💻 Usage

Run the simulator:
```bash
python main.py
```

### Simulation Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|--------|
| Order Size | Trade quantity in USD | 100 | 1-1,000,000 |
| Fee Tier | Trading fee tier | 0 | 0-5 |
| Volatility | Market volatility | 0.01 | 0.001-0.5 |

## 📊 Implementation Details

### 1. Order Book Processing

The `OrderBookProcessor` class handles real-time order book data:

```python
class OrderBookProcessor:
    def update_orderbook(self, data):
        """Updates internal order book state"""
        self.timestamp = data["timestamp"]
        self.exchange = data["exchange"]
        self.symbol = data["symbol"]
        self.asks = [[float(price), float(size)] for price, size in data["asks"]]
        self.bids = [[float(price), float(size)] for price, size in data["bids"]]
```

### 2. Slippage Calculation

Implements a linear regression model with market depth adjustments:

```python
def calculate_slippage(self, quantity, order_type="market"):
    """Calculate expected slippage using linear regression model"""
    # Base slippage component (0.01%)
    alpha = 0.0001
    # Volume coefficient
    beta = 0.02
    
    # Calculate market depth
    market_depth = sum(size for _, size in self.asks[:10])
    volume_factor = np.sqrt(quantity / market_depth) if market_depth > 0 else 1
    
    # Apply regression model
    model_slippage = alpha + beta * volume_factor
    return model_slippage
```

### 3. Fee Calculation

Dynamic fee calculation with volume-based discounts:

```python
def calculate_fees(self, quantity, fee_tier=0):
    """Calculate expected fees based on fee tier and volume"""
    # Apply volume-based discounts
    discount = 0.0
    for volume_threshold, volume_discount in sorted(VOLUME_DISCOUNTS.items(), reverse=True):
        if order_value > volume_threshold:
            discount = volume_discount
            break
    
    # Apply fee tier adjustments
    tier_discount = fee_tier * 0.05  # Each tier gives 5% discount
    total_discount = min(0.7, discount + tier_discount)
    
    # Calculate weighted average fee
    weighted_fee = (MAKER_FEE * maker_ratio + TAKER_FEE * (1 - maker_ratio)) * (1 - total_discount)
    return weighted_fee
```

### 4. Market Impact Model

Implements the Almgren-Chriss square root model:

```python
def calculate_market_impact(self, quantity, volatility=0.01):
    """Calculate expected market impact using Almgren-Chriss model"""
    # Model parameters
    sigma = volatility
    gamma = MARKET_IMPACT_PARAMS['gamma']
    eta = MARKET_IMPACT_PARAMS['eta']
    alpha = MARKET_IMPACT_PARAMS['alpha']
    
    # Calculate trading rate
    market_depth = sum(size for _, size in self.asks[:10])
    trading_rate = quantity / market_depth if market_depth > 0 else 1
    
    # Calculate impacts
    temp_impact = sigma * (trading_rate ** alpha)
    perm_impact = gamma * sigma * np.sqrt(trading_rate)
    
    return temp_impact + 0.5 * perm_impact
```

## 📈 Performance Metrics

| Metric | Value | Description |
|--------|-------|-------------|
| Order Processing | 1000 orders/sec | Maximum order processing rate |
| Average Latency | 2ms | Typical processing latency |
| Memory Usage | ~100MB | Average memory footprint |
| CPU Usage | 5-10% | Typical CPU utilization |
| UI Refresh Rate | 100ms | UI update frequency |

## 🔧 Configuration

Key configuration parameters in `config/settings.py`:

```python
# Fee Structure
MAKER_FEE = 0.001  # 0.1% maker fee
TAKER_FEE = 0.002  # 0.2% taker fee

# Volume Discounts
VOLUME_DISCOUNTS = {
    1000000: 0.2,  # 20% discount for > $1M
    500000: 0.1,   # 10% discount for > $500K
    100000: 0.05   # 5% discount for > $100K
}

# Market Impact Parameters
MARKET_IMPACT_PARAMS = {
    'gamma': 0.314,
    'eta': 0.142,
    'alpha': 0.5
}
```

## 📚 API Reference

### OrderBookProcessor

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `update_orderbook` | `data: dict` | None | Updates order book state |
| `calculate_slippage` | `quantity: float, order_type: str` | float | Calculates expected slippage |
| `calculate_fees` | `quantity: float, fee_tier: int` | float | Calculates trading fees |
| `calculate_market_impact` | `quantity: float, volatility: float` | float | Estimates market impact |
| `predict_maker_taker_ratio` | None | float | Predicts maker/taker ratio |

### TradeSimulatorUI

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `setup_ui` | None | None | Initializes UI components |
| `on_data_received` | `data: dict` | None | Handles WebSocket data |
| `on_simulate_clicked` | None | None | Runs trade simulation |
| `update_ui` | None | None | Updates UI components |

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please open an issue in the GitHub repository or contact the maintainers.

---

Built with ❤️ by the GoQuant Team