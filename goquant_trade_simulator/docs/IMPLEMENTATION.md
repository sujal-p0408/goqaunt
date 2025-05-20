# GoQuant Trade Simulator Implementation Guide

## Overview

This document provides a detailed guide to implementing the GoQuant Trade Simulator, including code examples, best practices, and implementation details for each component.

## Core Components Implementation

### 1. Order Book Processing

#### OrderBookProcessor Class

```python
class OrderBookProcessor:
    def __init__(self):
        self.asks = []
        self.bids = []
        self.timestamp = ""
        self.exchange = ""
        self.symbol = ""
        
    def update_orderbook(self, data):
        """Updates internal order book state with new data"""
        self.timestamp = data["timestamp"]
        self.exchange = data["exchange"]
        self.symbol = data["symbol"]
        self.asks = [[float(price), float(size)] for price, size in data["asks"]]
        self.bids = [[float(price), float(size)] for price, size in data["bids"]]
```

#### Slippage Calculation

```python
def calculate_slippage(self, quantity, order_type="market"):
    """Calculate expected slippage using linear regression model"""
    if not self.asks or not self.bids:
        return 0.0
        
    mid_price = (self.asks[0][0] + self.bids[0][0]) / 2
    
    if quantity <= 0:
        return 0.0
        
    # Simple order book traversal for market orders
    executed_qty = 0
    total_cost = 0
    
    if order_type == "market":
        # For a buy order, we walk up the asks
        for price, size in self.asks:
            if executed_qty >= quantity:
                break
                
            usable_size = min(size, quantity - executed_qty)
            total_cost += price * usable_size
            executed_qty += usable_size
            
        if executed_qty < quantity:
            # Not enough liquidity in the order book
            # Apply a penalty for the remaining quantity
            penalty_price = self.asks[-1][0] * 1.05  # 5% penalty
            total_cost += penalty_price * (quantity - executed_qty)
            executed_qty = quantity
            
        avg_execution_price = total_cost / quantity
        slippage_pct = (avg_execution_price - mid_price) / mid_price
        
        # Apply regression model
        alpha = 0.0001  # Base slippage component (0.01%)
        beta = 0.02     # Volume coefficient
        
        # Calculate market depth
        market_depth = sum(size for _, size in self.asks[:10])
        volume_factor = np.sqrt(quantity / market_depth) if market_depth > 0 else 1
        
        model_slippage = alpha + beta * volume_factor
        
        # Final slippage is max of simple calculation and model
        return max(slippage_pct, model_slippage)
    
    return 0.0
```

#### Fee Calculation

```python
def calculate_fees(self, quantity, fee_tier=0):
    """Calculate expected fees based on fee tier and volume"""
    if not self.asks or not self.bids:
        return 0.0
        
    mid_price = (self.asks[0][0] + self.bids[0][0]) / 2
    order_value = quantity * mid_price
    
    # Apply volume-based discounts
    discount = 0.0
    for volume_threshold, volume_discount in sorted(VOLUME_DISCOUNTS.items(), reverse=True):
        if order_value > volume_threshold:
            discount = volume_discount
            break
        
    # Apply fee tier adjustments
    tier_discount = fee_tier * 0.05  # Each tier gives 5% discount
    total_discount = min(0.7, discount + tier_discount)  # Cap at 70% discount
    
    # Get predicted maker/taker ratio
    maker_ratio = self.predict_maker_taker_ratio()
    
    # Calculate weighted average fee
    weighted_fee = (MAKER_FEE * maker_ratio + TAKER_FEE * (1 - maker_ratio)) * (1 - total_discount)
    total_fee = weighted_fee * order_value
    
    return total_fee / order_value  # Return as percentage of order value
```

#### Market Impact Calculation

```python
def calculate_market_impact(self, quantity, volatility=0.01):
    """Calculate expected market impact using Almgren-Chriss model"""
    if not self.asks or not self.bids:
        return 0.0
        
    mid_price = (self.asks[0][0] + self.bids[0][0]) / 2
    
    # Almgren-Chriss model parameters
    sigma = volatility  # Price volatility
    gamma = MARKET_IMPACT_PARAMS['gamma']
    eta = MARKET_IMPACT_PARAMS['eta']
    alpha = MARKET_IMPACT_PARAMS['alpha']
    
    # Calculate market depth
    market_depth = sum(size for _, size in self.asks[:10])
    
    # Calculate trading rate
    trading_rate = quantity / market_depth if market_depth > 0 else 1
    
    # Temporary impact
    temp_impact = sigma * (trading_rate ** alpha)
    
    # Permanent impact
    perm_impact = gamma * sigma * np.sqrt(trading_rate)
    
    # Total impact (weighted sum)
    total_impact = temp_impact + 0.5 * perm_impact
    
    return total_impact
```

### 2. UI Implementation

#### Main Window Setup

```python
class TradeSimulatorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Initialize components
        self.processor = OrderBookProcessor()
        self.ws_thread = WebSocketThread(WS_URL)
        
        # Set up UI
        self.setup_ui()
        
        # Start WebSocket connection
        self.ws_thread.data_received.connect(self.on_data_received)
        self.ws_thread.latency_updated.connect(self.on_latency_updated)
        self.ws_thread.start()
        
        # Set up update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(UI_UPDATE_INTERVAL)
```

#### UI Component Setup

```python
def setup_ui(self):
    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    
    main_layout = QHBoxLayout(central_widget)
    
    # Left panel (input parameters)
    input_group = QGroupBox("Input Parameters")
    input_layout = QGridLayout()
    input_group.setLayout(input_layout)
    
    # Add input components
    self.setup_input_components(input_layout)
    
    # Right panel (output parameters)
    output_group = QGroupBox("Output Parameters")
    output_layout = QGridLayout()
    output_group.setLayout(output_layout)
    
    # Add output components
    self.setup_output_components(output_layout)
    
    # Add panels to main layout
    main_layout.addWidget(input_group, 1)
    main_layout.addWidget(output_group, 1)
```

#### Input Components Setup

```python
def setup_input_components(self, layout):
    # Exchange selection
    layout.addWidget(QLabel("Exchange:"), 0, 0)
    self.exchange_combo = QComboBox()
    self.exchange_combo.addItem("OKX")
    layout.addWidget(self.exchange_combo, 0, 1)
    
    # Asset selection
    layout.addWidget(QLabel("Spot Asset:"), 1, 0)
    self.asset_combo = QComboBox()
    self.asset_combo.addItems(["BTC-USDT", "ETH-USDT", "XRP-USDT", "SOL-USDT"])
    layout.addWidget(self.asset_combo, 1, 1)
    
    # Order type selection
    layout.addWidget(QLabel("Order Type:"), 2, 0)
    self.order_type_combo = QComboBox()
    self.order_type_combo.addItem("Market")
    layout.addWidget(self.order_type_combo, 2, 1)
    
    # Quantity input
    layout.addWidget(QLabel("Quantity (USD):"), 3, 0)
    self.quantity_spin = QDoubleSpinBox()
    self.quantity_spin.setRange(1, 1000000)
    self.quantity_spin.setValue(100)
    self.quantity_spin.setSingleStep(10)
    layout.addWidget(self.quantity_spin, 3, 1)
    
    # Volatility input
    layout.addWidget(QLabel("Volatility:"), 4, 0)
    self.volatility_spin = QDoubleSpinBox()
    self.volatility_spin.setRange(0.001, 0.5)
    self.volatility_spin.setValue(DEFAULT_VOLATILITY)
    self.volatility_spin.setSingleStep(0.001)
    self.volatility_spin.setDecimals(3)
    layout.addWidget(self.volatility_spin, 4, 1)
    
    # Fee tier input
    layout.addWidget(QLabel("Fee Tier:"), 5, 0)
    self.fee_tier_spin = QDoubleSpinBox()
    self.fee_tier_spin.setRange(0, 5)
    self.fee_tier_spin.setValue(DEFAULT_FEE_TIER)
    self.fee_tier_spin.setSingleStep(1)
    layout.addWidget(self.fee_tier_spin, 5, 1)
    
    # Simulate button
    self.simulate_btn = QPushButton("Simulate Trade")
    self.simulate_btn.clicked.connect(self.on_simulate_clicked)
    layout.addWidget(self.simulate_btn, 6, 0, 1, 2)
```

#### Output Components Setup

```python
def setup_output_components(self, layout):
    # Slippage output
    layout.addWidget(QLabel("Expected Slippage:"), 0, 0)
    self.slippage_output = QLineEdit("0.0000%")
    self.slippage_output.setReadOnly(True)
    layout.addWidget(self.slippage_output, 0, 1)
    
    # Fees output
    layout.addWidget(QLabel("Expected Fees:"), 1, 0)
    self.fees_output = QLineEdit("0.0000%")
    self.fees_output.setReadOnly(True)
    layout.addWidget(self.fees_output, 1, 1)
    
    # Market impact output
    layout.addWidget(QLabel("Expected Market Impact:"), 2, 0)
    self.impact_output = QLineEdit("0.0000%")
    self.impact_output.setReadOnly(True)
    layout.addWidget(self.impact_output, 2, 1)
    
    # Net cost output
    layout.addWidget(QLabel("Net Cost:"), 3, 0)
    self.net_cost_output = QLineEdit("0.0000%")
    self.net_cost_output.setReadOnly(True)
    layout.addWidget(self.net_cost_output, 3, 1)
    
    # Maker/taker ratio output
    layout.addWidget(QLabel("Maker/Taker Proportion:"), 4, 0)
    self.maker_taker_output = QLineEdit("50% / 50%")
    self.maker_taker_output.setReadOnly(True)
    layout.addWidget(self.maker_taker_output, 4, 1)
    
    # Latency output
    layout.addWidget(QLabel("Internal Latency:"), 5, 0)
    self.latency_output = QLineEdit("0.00 ms")
    self.latency_output.setReadOnly(True)
    layout.addWidget(self.latency_output, 5, 1)
```

### 3. WebSocket Implementation

#### WebSocket Thread

```python
class WebSocketThread(QThread):
    data_received = pyqtSignal(dict)
    latency_updated = pyqtSignal(float)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.connection_active = False
        self.running = True
        
    def run(self):
        while self.running:
            try:
                ws = websocket.WebSocketApp(
                    self.url,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )
                ws.run_forever()
            except Exception as e:
                print(f"WebSocket error: {e}")
                time.sleep(5)  # Reconnection delay
                
    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.data_received.emit(data)
            
            # Calculate latency
            latency = (time.time() - data['timestamp']) * 1000
            self.latency_updated.emit(latency)
            
        except Exception as e:
            print(f"Message processing error: {e}")
            
    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")
        self.connection_active = False
        
    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")
        self.connection_active = False
        
    def stop(self):
        self.running = False
        self.wait()
```

## Best Practices

### 1. Error Handling

```python
def safe_operation(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")
            return None
    return wrapper
```

### 2. Performance Optimization

```python
@lru_cache(maxsize=1000)
def calculate_slippage(quantity, order_type="market"):
    # Slippage calculation logic
    pass
```

### 3. Memory Management

```python
def cleanup_old_data(self):
    if len(self.order_history) > 1000:
        self.order_history = self.order_history[-1000:]
```

### 4. UI Updates

```python
def update_ui(self):
    if not self._update_pending:
        self._update_pending = True
        QTimer.singleShot(100, self._do_update)

def _do_update(self):
    # Perform actual UI update
    self._update_pending = False
```

## Testing

### 1. Unit Tests

```python
def test_slippage_calculation():
    processor = OrderBookProcessor()
    data = {
        "timestamp": "2024-03-20T10:00:00Z",
        "exchange": "OKX",
        "symbol": "BTC-USDT",
        "asks": [[50000.0, 1.5], [50001.0, 2.0]],
        "bids": [[49999.0, 1.0], [49998.0, 2.5]]
    }
    processor.update_orderbook(data)
    slippage = processor.calculate_slippage(1.0)
    assert 0 <= slippage <= 0.1  # Slippage should be between 0% and 10%
```

### 2. Integration Tests

```python
def test_ui_updates():
    app = QApplication([])
    ui = TradeSimulatorUI()
    
    # Simulate data reception
    data = {
        "timestamp": "2024-03-20T10:00:00Z",
        "exchange": "OKX",
        "symbol": "BTC-USDT",
        "asks": [[50000.0, 1.5], [50001.0, 2.0]],
        "bids": [[49999.0, 1.0], [49998.0, 2.5]]
    }
    ui.on_data_received(data)
    
    # Verify UI updates
    assert ui.orderbook_status.text() == "Order Book: 2 bids, 2 asks"
```

## Deployment

### 1. Requirements

```txt
PyQt5>=5.15.0
websocket-client>=1.2.0
numpy>=1.19.0
pandas>=1.2.0
scipy>=1.6.0
matplotlib>=3.3.0
```

### 2. Configuration

```python
# config/settings.py
WINDOW_TITLE = "GoQuant Trade Simulator"
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
UI_UPDATE_INTERVAL = 100  # ms
WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
```

### 3. Running the Application

```python
# main.py
from PyQt5.QtWidgets import QApplication
from simulator.ui import TradeSimulatorUI
import sys

def main():
    app = QApplication(sys.argv)
    window = TradeSimulatorUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 