# WebSocket Configuration
WS_URL = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"

# UI Configuration
WINDOW_TITLE = "GoQuant Trade Simulator"
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 600
UI_UPDATE_INTERVAL = 500  # milliseconds

# Trading Parameters
DEFAULT_FEE_TIER = 0
DEFAULT_VOLATILITY = 0.01

# Fee Structure
MAKER_FEE = 0.0002  # 0.02%
TAKER_FEE = 0.0005  # 0.05%

# Volume-based Discounts
VOLUME_DISCOUNTS = {
    1_000_000: 0.2,  # 20% discount for > $1M
    100_000: 0.1,    # 10% discount for > $100K
}

# Market Impact Model Parameters
MARKET_IMPACT_PARAMS = {
    'gamma': 0.314,  # Market response parameter
    'eta': 0.142,    # Market resilience
    'alpha': 0.2,    # Concavity parameter
}

# Maker/Taker Ratio Parameters
MAKER_TAKER_PARAMS = {
    'k': 4.0,        # Steepness parameter
    'x0': 0.0,       # Midpoint parameter
} 