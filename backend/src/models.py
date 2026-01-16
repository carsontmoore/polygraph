"""
Pydantic models for Polygraph data structures.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# Polymarket API Response Models
# ============================================================================

class PolymarketToken(BaseModel):
    """Token within a market (YES/NO outcome)."""
    token_id: str
    outcome: str
    price: float


class PolymarketMarket(BaseModel):
    """Market data from Polymarket Gamma API."""
    id: str
    question: str
    condition_id: str
    slug: str
    outcomes: list[str]
    outcome_prices: list[str] = Field(alias="outcomePrices", default=[])
    volume: str = "0"
    liquidity: str = "0"
    end_date: Optional[datetime] = Field(alias="endDateIso", default=None)
    active: bool = True
    closed: bool = False
    
    class Config:
        populate_by_name = True


class OrderbookEntry(BaseModel):
    """Single entry in orderbook (bid or ask)."""
    price: str
    size: str


class Orderbook(BaseModel):
    """Orderbook snapshot from CLOB API."""
    market: str
    asset_id: str
    bids: list[OrderbookEntry] = []
    asks: list[OrderbookEntry] = []
    timestamp: Optional[str] = None
    hash: Optional[str] = None


# ============================================================================
# Internal Models
# ============================================================================

class Market(BaseModel):
    """Internal market representation."""
    id: str
    condition_id: str
    question: str
    slug: str
    outcomes: list[str]
    yes_token_id: Optional[str] = None
    no_token_id: Optional[str] = None
    yes_price: float = 0.5
    no_price: float = 0.5
    volume_24h: float = 0.0
    liquidity: float = 0.0
    end_date: Optional[datetime] = None
    is_active: bool = True
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class PriceSnapshot(BaseModel):
    """Point-in-time price data."""
    market_id: str
    timestamp: datetime
    yes_price: float
    no_price: float
    volume: float
    bid_depth: float = 0.0
    ask_depth: float = 0.0


class Signal(BaseModel):
    """Detected signal."""
    id: Optional[int] = None
    market_id: str
    signal_type: str  # 'volume_spike', 'price_divergence', 'orderbook_imbalance'
    timestamp: datetime
    score: float  # 0-100
    details: dict = {}
    
    # Snapshot at time of signal
    price_at_signal: float
    volume_at_signal: float
    
    class Config:
        from_attributes = True


# ============================================================================
# API Response Models
# ============================================================================

class MarketSummary(BaseModel):
    """Summary for market list view."""
    id: str
    question: str
    slug: str
    yes_price: float
    volume_24h: float
    recent_signals: int = 0
    last_signal_at: Optional[datetime] = None


class SignalResponse(BaseModel):
    """Signal for API response."""
    id: int
    market_id: str
    market_question: str
    signal_type: str
    timestamp: datetime
    score: float
    details: dict
    price_at_signal: float


class DashboardStats(BaseModel):
    """Stats for dashboard."""
    total_markets_tracked: int
    signals_24h: int
    highest_score_signal: Optional[SignalResponse] = None
    most_active_market: Optional[MarketSummary] = None
