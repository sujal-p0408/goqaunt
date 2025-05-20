import numpy as np
from config.settings import (
    MAKER_FEE, TAKER_FEE, VOLUME_DISCOUNTS,
    MARKET_IMPACT_PARAMS, MAKER_TAKER_PARAMS
)

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
        
        # Apply volume-based discounts
        discount = 0.0
        for volume_threshold, volume_discount in sorted(VOLUME_DISCOUNTS.items(), reverse=True):
            if order_value > volume_threshold:
                discount = volume_discount
                break
            
        # Apply fee tier adjustments (simplified)
        tier_discount = fee_tier * 0.05  # Each tier gives 5% discount
        total_discount = min(0.7, discount + tier_discount)  # Cap at 70% discount
        
        # Get predicted maker/taker ratio
        maker_ratio = self.predict_maker_taker_ratio()
        
        # Calculate weighted average fee
        weighted_fee = (MAKER_FEE * maker_ratio + TAKER_FEE * (1 - maker_ratio)) * (1 - total_discount)
        total_fee = weighted_fee * order_value
        
        return total_fee / order_value  # Return as percentage of order value
    
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
        k = MAKER_TAKER_PARAMS['k']
        x0 = MAKER_TAKER_PARAMS['x0']
        maker_ratio = 1 / (1 + np.exp(-k * (imbalance - x0)))
        
        return maker_ratio 