from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QComboBox, QDoubleSpinBox, QPushButton,
                            QGroupBox, QGridLayout, QLineEdit)
from PyQt5.QtCore import Qt, QTimer
from config.settings import (
    WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    UI_UPDATE_INTERVAL, WS_URL, DEFAULT_FEE_TIER, DEFAULT_VOLATILITY
)
from .processor import OrderBookProcessor
from .websocket_thread import WebSocketThread

class TradeSimulatorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Initialize data processor
        self.processor = OrderBookProcessor()
        
        # Initialize performance metrics
        self.latency_values = []
        self.max_latency = 0
        self.avg_latency = 0
        
        # Set up the UI
        self.setup_ui()
        
        # Start WebSocket connection
        self.ws_thread = WebSocketThread(WS_URL)
        self.ws_thread.data_received.connect(self.on_data_received)
        self.ws_thread.latency_updated.connect(self.on_latency_updated)
        self.ws_thread.start()
        
        # Set up a timer to update UI periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(UI_UPDATE_INTERVAL)
    
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
        self.volatility_spin.setValue(DEFAULT_VOLATILITY)
        self.volatility_spin.setSingleStep(0.001)
        self.volatility_spin.setDecimals(3)
        input_layout.addWidget(self.volatility_spin, 4, 1)
        
        # Fee Tier
        input_layout.addWidget(QLabel("Fee Tier:"), 5, 0)
        self.fee_tier_spin = QDoubleSpinBox()
        self.fee_tier_spin.setRange(0, 5)
        self.fee_tier_spin.setValue(DEFAULT_FEE_TIER)
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
        self.ws_thread.stop()
        event.accept() 