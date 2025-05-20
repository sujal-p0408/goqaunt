# GoQuant Trade Simulator API Documentation

## Core Classes and Methods

### OrderBookProcessor

The main class responsible for processing order book data and calculating trading metrics.

#### Methods

##### `update_orderbook(data: dict) -> None`
Updates the internal order book state with new data.

**Parameters:**
- `data` (dict): Order book data containing:
  - `timestamp` (str): Current timestamp
  - `exchange` (str): Exchange name
  - `symbol` (str): Trading pair
  - `asks` (list): List of [price, size] pairs for asks
  - `bids` (list): List of [price, size] pairs for bids

**Example:**
```python
data = {
    "timestamp": "2024-03-20T10:00:00Z",
    "exchange": "OKX",
    "symbol": "BTC-USDT",
    "asks": [[50000.0, 1.5], [50001.0, 2.0]],
    "bids": [[49999.0, 1.0], [49998.0, 2.5]]
}
processor.update_orderbook(data)
```

##### `calculate_slippage(quantity: float, order_type: str = "market") -> float`
Calculates expected slippage for a given order size.

**Parameters:**
- `quantity` (float): Order size in base currency
- `order_type` (str): Type of order ("market" or "limit")

**Returns:**
- `float`: Expected slippage as a decimal (e.g., 0.001 for 0.1%)

**Example:**
```python
slippage = processor.calculate_slippage(1.5)  # Calculate slippage for 1.5 BTC
```

##### `calculate_fees(quantity: float, fee_tier: int = 0) -> float`
Calculates trading fees based on order size and fee tier.

**Parameters:**
- `quantity` (float): Order size in base currency
- `fee_tier` (int): Fee tier (0-5)

**Returns:**
- `float`: Fee as a decimal of order value

**Example:**
```python
fee = processor.calculate_fees(1.5, fee_tier=2)  # Calculate fees for 1.5 BTC with tier 2
```

##### `calculate_market_impact(quantity: float, volatility: float = 0.01) -> float`
Estimates market impact using the Almgren-Chriss model.

**Parameters:**
- `quantity` (float): Order size in base currency
- `volatility` (float): Market volatility parameter

**Returns:**
- `float`: Expected market impact as a decimal

**Example:**
```python
impact = processor.calculate_market_impact(1.5, volatility=0.015)
```

##### `predict_maker_taker_ratio() -> float`
Predicts the maker/taker ratio based on order book imbalance.

**Returns:**
- `float`: Predicted maker ratio (0-1)

**Example:**
```python
maker_ratio = processor.predict_maker_taker_ratio()
```

### TradeSimulatorUI

The main UI class that handles the graphical interface and user interactions.

#### Methods

##### `setup_ui() -> None`
Initializes and sets up the UI components.

**Example:**
```python
ui = TradeSimulatorUI()
ui.setup_ui()
```

##### `on_data_received(data: dict) -> None`
Handles incoming WebSocket data.

**Parameters:**
- `data` (dict): Order book data from WebSocket

**Example:**
```python
data = {
    "timestamp": "2024-03-20T10:00:00Z",
    "exchange": "OKX",
    "symbol": "BTC-USDT",
    "asks": [[50000.0, 1.5], [50001.0, 2.0]],
    "bids": [[49999.0, 1.0], [49998.0, 2.5]]
}
ui.on_data_received(data)
```

##### `on_simulate_clicked() -> None`
Handles simulation button click event.

**Example:**
```python
ui.on_simulate_clicked()  # Trigger simulation
```

##### `update_ui() -> None`
Updates UI components with latest data.

**Example:**
```python
ui.update_ui()  # Refresh UI
```

### WebSocketThread

Handles WebSocket connection and data streaming.

#### Methods

##### `run() -> None`
Main thread execution method.

**Example:**
```python
ws_thread = WebSocketThread(WS_URL)
ws_thread.start()  # Starts the WebSocket thread
```

##### `stop() -> None`
Stops the WebSocket thread.

**Example:**
```python
ws_thread.stop()  # Stops the WebSocket thread
```

## Configuration Parameters

### Window Settings
```python
WINDOW_TITLE = "GoQuant Trade Simulator"
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
```

### API Settings
```python
WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
```

### Fee Structure
```python
MAKER_FEE = 0.001  # 0.1%
TAKER_FEE = 0.002  # 0.2%
```

### Volume Discounts
```python
VOLUME_DISCOUNTS = {
    1000000: 0.2,  # 20% discount for > $1M
    500000: 0.1,   # 10% discount for > $500K
    100000: 0.05   # 5% discount for > $100K
}
```

### Market Impact Parameters
```python
MARKET_IMPACT_PARAMS = {
    'gamma': 0.314,  # Permanent impact coefficient
    'eta': 0.142,    # Temporary impact coefficient
    'alpha': 0.5     # Power law exponent
}
```

## Error Handling

### WebSocket Errors
```python
try:
    ws = websocket.WebSocketApp(url, on_message=on_message)
    ws.run_forever()
except Exception as e:
    print(f"WebSocket error: {e}")
    time.sleep(5)  # Reconnection delay
```

### Data Processing Errors
```python
try:
    processor.update_orderbook(data)
except ValueError as e:
    print(f"Invalid data format: {e}")
except Exception as e:
    print(f"Processing error: {e}")
```

### UI Errors
```python
try:
    ui.update_ui()
except Exception as e:
    print(f"UI update error: {e}")
    # Fallback to last known good state
```

## Performance Optimization

### Caching
```python
@lru_cache(maxsize=1000)
def calculate_slippage(quantity, order_type="market"):
    # Slippage calculation logic
    pass
```

### Batched Updates
```python
def update_ui(self):
    if not self._update_pending:
        self._update_pending = True
        QTimer.singleShot(100, self._do_update)

def _do_update(self):
    # Perform actual UI update
    self._update_pending = False
```

### Memory Management
```python
def cleanup_old_data(self):
    if len(self.order_history) > 1000:
        self.order_history = self.order_history[-1000:]
``` 