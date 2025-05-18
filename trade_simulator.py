import sys
import json
import time
import threading
import websocket
import ssl
import numpy as np
import pandas as pd
from scipy import stats
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox,
                            QPushButton, QGroupBox, QGridLayout, QLineEdit)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer

class OrderBookProcessor:
    def __init__(self):
        self.asks = []
        self.bids = []
        self.timestamp = ""
        self.exchange = ""
        self.symbol = ""
        
    def update_orderbook(self, data):
        self.timestamp = data["timestamp"]
        self.exchange = data["exchange"]
        self.symbol = data["symbol"]
        self.asks = [[float(price), float(size)] for price, size in data["asks"]]
        self.bids = [[float(price), float(size)] for price, size in data["bids"]]
    
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
            # slippage = α + β × f(volume_factor, price_difference)
            alpha = 0.0001  # Base slippage component (0.01%)
            beta = 0.02     # Volume coefficient
            
            # Calculate market depth (sum of visible liquidity in first 10 levels)
            market_depth = sum(size for _, size in self.asks[:10])
            volume_factor = np.sqrt(quantity / market_depth) if market_depth > 0 else 1
            
            model_slippage = alpha + beta * volume_factor
            
            # Final slippage is max of simple calculation and model
            return max(slippage_pct, model_slippage)
        
        return 0.0
    
    def calculate_fees(self, quantity, fee_tier=0):
        """Calculate expected fees based on fee tier"""
        if not self.asks or not self.bids:
            return 0.0
            
        mid_price = (self.asks[0][0] + self.bids[0][0]) / 2
        order_value = quantity * mid_price
        
        # Base fee rates
        maker_fee = 0.0002  # 0.02%
        taker_fee = 0.0005  # 0.05%
        
        # Apply volume-based discounts
        if order_value > 1_000_000:  # > $1M
            discount = 0.2  # 20% discount
        elif order_value > 100_000:  # > $100K
            discount = 0.1  # 10% discount
        else:
            discount = 0.0
            
        # Apply fee tier adjustments (simplified)
        tier_discount = fee_tier * 0.05  # Each tier gives 5% discount
        total_discount = min(0.7, discount + tier_discount)  # Cap at 70% discount
        
        # Get predicted maker/taker ratio
        maker_ratio = self.predict_maker_taker_ratio()
        
        # Calculate weighted average fee
        weighted_fee = (maker_fee * maker_ratio + taker_fee * (1 - maker_ratio)) * (1 - total_discount)
        total_fee = weighted_fee * order_value
        
        return total_fee / order_value  # Return as percentage of order value
    
    def calculate_market_impact(self, quantity, volatility=0.01):
        """Calculate expected market impact using Almgren-Chriss model"""
        if not self.asks or not self.bids:
            return 0.0
            
        mid_price = (self.asks[0][0] + self.bids[0][0]) / 2
        
        # Almgren-Chriss model parameters
        sigma = volatility  # Price volatility
        gamma = 0.314       # Market response parameter
        eta = 0.142         # Market resilience
        alpha = 0.2         # Concavity parameter
        
        # Calculate market depth
        market_depth = sum(size for _, size in self.asks[:10])
        
        # Calculate trading rate (simplified as quantity / market depth)
        trading_rate = quantity / market_depth if market_depth > 0 else 1
        
        # Temporary impact
        temp_impact = sigma * (trading_rate ** alpha)
        
        # Permanent impact
        perm_impact = gamma * sigma * np.sqrt(trading_rate)
        
        # Total impact (weighted sum)
        total_impact = temp_impact + 0.5 * perm_impact
        
        return total_impact
    
    def predict_maker_taker_ratio(self):
        """Predict maker/taker ratio using logistic regression on order book imbalance"""
        if not self.asks or not self.bids:
            return 0.5  # Default 50/50
            
        # Calculate bid/ask volume imbalance
        bid_volume = sum(size for _, size in self.bids[:5])
        ask_volume = sum(size for _, size in self.asks[:5])
        
        if bid_volume + ask_volume == 0:
            return 0.5
            
        imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
        
        # Apply logistic function
        k = 4.0       # Steepness parameter
        x0 = 0.0      # Midpoint parameter
        maker_ratio = 1 / (1 + np.exp(-k * (imbalance - x0)))
        
        return maker_ratio

class WebSocketThread(QThread):
    data_received = pyqtSignal(dict)
    latency_updated = pyqtSignal(float)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = True
        self.connection_active = False
        
    def run(self):
        def on_message(ws, message):
            start_time = time.time()
            try:
                data = json.loads(message)
                self.connection_active = True
                self.data_received.emit(data)
                
                # Calculate processing latency
                processing_time = (time.time() - start_time) * 1000  # in ms
                self.latency_updated.emit(processing_time)
            except Exception as e:
                print(f"Error processing message: {e}")
            
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
            self.connection_active = False
        
        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket closed: {close_status_code} - {close_msg}")
            self.connection_active = False
            
            # Attempt to reconnect after a delay if thread is still running
            if self.running:
                time.sleep(5)
                self.connect_websocket()
        
        def on_open(ws):
            print("WebSocket connection opened")
            self.connection_active = True
        
        def connect_websocket():
            wsapp = websocket.WebSocketApp(self.url,
                                          on_open=on_open,
                                          on_message=on_message,
                                          on_error=on_error,
                                          on_close=on_close)
            wsapp.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        self.connect_websocket = connect_websocket
        connect_websocket()

class TradeSimulatorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoQuant Trade Simulator")
        self.setMinimumSize(1000, 600)
        
        # Initialize data processor
        self.processor = OrderBookProcessor()
        
        # Initialize performance metrics
        self.latency_values = []
        self.max_latency = 0
        self.avg_latency = 0
        
        # Set up the UI
        self.setup_ui()
        
        # Start WebSocket connection
        self.ws_url = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"
        self.ws_thread = WebSocketThread(self.ws_url)
        self.ws_thread.data_received.connect(self.on_data_received)
        self.ws_thread.latency_updated.connect(self.on_latency_updated)
        self.ws_thread.start()
        
        # Set up a timer to update UI periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(500)  # Update every 500ms
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel (input parameters)
        input_group = QGroupBox("Input Parameters")
        input_layout = QGridLayout()
        input_group.setLayout(input_layout)
        
        # Exchange
        input_layout.addWidget(QLabel("Exchange:"), 0, 0)
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItem("OKX")
        input_layout.addWidget(self.exchange_combo, 0, 1)
        
        # Asset
        input_layout.addWidget(QLabel("Spot Asset:"), 1, 0)
        self.asset_combo = QComboBox()
        self.asset_combo.addItems(["BTC-USDT", "ETH-USDT", "XRP-USDT", "SOL-USDT"])
        input_layout.addWidget(self.asset_combo, 1, 1)
        
        # Order Type
        input_layout.addWidget(QLabel("Order Type:"), 2, 0)
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItem("Market")
        input_layout.addWidget(self.order_type_combo, 2, 1)
        
        # Quantity
        input_layout.addWidget(QLabel("Quantity (USD):"), 3, 0)
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(1, 1000000)
        self.quantity_spin.setValue(100)
        self.quantity_spin.setSingleStep(10)
        input_layout.addWidget(self.quantity_spin, 3, 1)
        
        # Volatility
        input_layout.addWidget(QLabel("Volatility:"), 4, 0)
        self.volatility_spin = QDoubleSpinBox()
        self.volatility_spin.setRange(0.001, 0.5)
        self.volatility_spin.setValue(0.01)
        self.volatility_spin.setSingleStep(0.001)
        self.volatility_spin.setDecimals(3)
        input_layout.addWidget(self.volatility_spin, 4, 1)
        
        # Fee Tier
        input_layout.addWidget(QLabel("Fee Tier:"), 5, 0)
        self.fee_tier_spin = QDoubleSpinBox()
        self.fee_tier_spin.setRange(0, 5)
        self.fee_tier_spin.setValue(0)
        self.fee_tier_spin.setSingleStep(1)
        input_layout.addWidget(self.fee_tier_spin, 5, 1)
        
        # Simulate button
        self.simulate_btn = QPushButton("Simulate Trade")
        self.simulate_btn.clicked.connect(self.on_simulate_clicked)
        input_layout.addWidget(self.simulate_btn, 6, 0, 1, 2)
        
        # Connection status
        self.connection_status = QLabel("Connection Status: Connecting...")
        input_layout.addWidget(self.connection_status, 7, 0, 1, 2)
        
        # Right panel (output parameters)
        output_group = QGroupBox("Output Parameters")
        output_layout = QGridLayout()
        output_group.setLayout(output_layout)
        
        # Labels for outputs
        output_layout.addWidget(QLabel("Expected Slippage:"), 0, 0)
        self.slippage_output = QLineEdit("0.0000%")
        self.slippage_output.setReadOnly(True)
        output_layout.addWidget(self.slippage_output, 0, 1)
        
        output_layout.addWidget(QLabel("Expected Fees:"), 1, 0)
        self.fees_output = QLineEdit("0.0000%")
        self.fees_output.setReadOnly(True)
        output_layout.addWidget(self.fees_output, 1, 1)
        
        output_layout.addWidget(QLabel("Expected Market Impact:"), 2, 0)
        self.impact_output = QLineEdit("0.0000%")
        self.impact_output.setReadOnly(True)
        output_layout.addWidget(self.impact_output, 2, 1)
        
        output_layout.addWidget(QLabel("Net Cost:"), 3, 0)
        self.net_cost_output = QLineEdit("0.0000%")
        self.net_cost_output.setReadOnly(True)
        output_layout.addWidget(self.net_cost_output, 3, 1)
        
        output_layout.addWidget(QLabel("Maker/Taker Proportion:"), 4, 0)
        self.maker_taker_output = QLineEdit("50% / 50%")
        self.maker_taker_output.setReadOnly(True)
        output_layout.addWidget(self.maker_taker_output, 4, 1)
        
        output_layout.addWidget(QLabel("Internal Latency:"), 5, 0)
        self.latency_output = QLineEdit("0.00 ms")
        self.latency_output.setReadOnly(True)
        output_layout.addWidget(self.latency_output, 5, 1)
        
        # Add orderbook status
        output_layout.addWidget(QLabel("Order Book Status:"), 6, 0)
        self.orderbook_status = QLineEdit("Waiting for data...")
        self.orderbook_status.setReadOnly(True)
        output_layout.addWidget(self.orderbook_status, 6, 1)
        
        # Add panels to main layout
        main_layout.addWidget(input_group, 1)
        main_layout.addWidget(output_group, 1)
    
    def on_data_received(self, data):
        self.processor.update_orderbook(data)
        
        # Update connection status
        self.connection_status.setText(f"Connection Status: Connected to {data['exchange']} {data['symbol']}")
        
        # Update orderbook status
        num_asks = len(data["asks"])
        num_bids = len(data["bids"])
        self.orderbook_status.setText(f"Order Book: {num_bids} bids, {num_asks} asks")
    
    def on_latency_updated(self, latency_ms):
        # Update latency metrics
        self.latency_values.append(latency_ms)
        if len(self.latency_values) > 100:
            self.latency_values.pop(0)
            
        self.max_latency = max(self.max_latency, latency_ms)
        self.avg_latency = sum(self.latency_values) / len(self.latency_values)
        
        # Update latency display
        self.latency_output.setText(f"{self.avg_latency:.2f} ms (max: {self.max_latency:.2f} ms)")
    
    def on_simulate_clicked(self):
        # Get input parameters
        quantity = self.quantity_spin.value()
        volatility = self.volatility_spin.value()
        fee_tier = self.fee_tier_spin.value()
        
        # Calculate outputs
        slippage = self.processor.calculate_slippage(quantity)
        fees = self.processor.calculate_fees(quantity, fee_tier)
        market_impact = self.processor.calculate_market_impact(quantity, volatility)
        
        # Calculate net cost
        net_cost = slippage + fees + market_impact
        
        # Calculate maker/taker ratio
        maker_ratio = self.processor.predict_maker_taker_ratio()
        taker_ratio = 1 - maker_ratio
        
        # Update output displays
        self.slippage_output.setText(f"{slippage*100:.4f}%")
        self.fees_output.setText(f"{fees*100:.4f}%")
        self.impact_output.setText(f"{market_impact*100:.4f}%")
        self.net_cost_output.setText(f"{net_cost*100:.4f}%")
        self.maker_taker_output.setText(f"{maker_ratio*100:.1f}% / {taker_ratio*100:.1f}%")
    
    def update_ui(self):
        # Update connection status if WebSocket is disconnected
        if not self.ws_thread.connection_active:
            self.connection_status.setText("Connection Status: Disconnected (attempting to reconnect)")
    
    def closeEvent(self, event):
        # Stop the WebSocket thread when window is closed
        self.ws_thread.running = False
        self.ws_thread.quit()
        self.ws_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradeSimulatorUI()
    window.show()
    sys.exit(app.exec_()) 