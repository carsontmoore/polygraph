"""
Pydantic models for Polygraph data structures.

LEARNING NOTE: Pydantic Models
==============================
Pydantic is a data validation library that uses Python type hints.
When you define a model like:

    class User(BaseModel):
        name: str
        age: int

Pydantic will:
1. Validate that incoming data matches these types
2. Convert data where possible (e.g., "42" -> 42 for int fields)
3. Raise clear errors when validation fails

Key concepts used in this file:
- Field(): Customize field behavior (aliases, defaults)
- field_validator(): Transform data BEFORE validation
- model_config: Configure model-wide behavior
- Optional[]: Field can be None
- Properties: Computed values that aren't stored
"""

from datetime import datetime
from typing import Optional, Any
import json
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# Polymarket API Response Models
# ============================================================================

class PolymarketToken(BaseModel):
    """Token within a market (YES/NO outcome)."""
    token_id: str
    outcome: str
    price: float


class PolymarketMarket(BaseModel):
    """
    Market data from Polymarket Gamma API.
    
    LEARNING NOTE: Handling Messy APIs
    ==================================
    Real-world APIs often return inconsistent data:
    - Fields might be camelCase or snake_case
    - Lists might come as JSON strings: '["a", "b"]' instead of ["a", "b"]
    - Numbers might be strings or vice versa
    - Fields might be missing entirely
    
    Pydantic validators let us normalize this mess before validation.
    The `mode='before'` means "run this BEFORE type checking".
    """
    
    # Model configuration (Pydantic v2 style)
    model_config = ConfigDict(
        populate_by_name=True,  # Accept both "conditionId" and "condition_id"
        extra="ignore",         # Don't fail on unexpected fields
    )
    
    # Core identifiers - at least one should be present
    id: Optional[str] = None
    condition_id: Optional[str] = Field(alias="conditionId", default=None)
    slug: Optional[str] = None
    
    # Market info
    question: Optional[str] = None
    title: Optional[str] = None
    outcomes: list[str] = []
    outcome_prices: list[str] = Field(alias="outcomePrices", default=[])
    
    # Metrics - these come as various types, we normalize to strings
    volume: str = "0"
    volume_24hr: str = Field(alias="volume24hr", default="0")
    liquidity: str = "0"
    
    # Status
    active: bool = True
    closed: bool = False
    archived: bool = False
    
    # Timestamps
    end_date: Optional[str] = Field(alias="endDate", default=None)
    end_date_iso: Optional[str] = Field(alias="endDateIso", default=None)
    
    # Token info (for CLOB API access)
    clob_token_ids: list[str] = Field(alias="clobTokenIds", default=[])
    tokens: Optional[list[dict]] = None
    
    # -------------------------------------------------------------------------
    # VALIDATORS: Transform data before Pydantic validates types
    # -------------------------------------------------------------------------
    
    @field_validator('outcomes', 'outcome_prices', 'clob_token_ids', mode='before')
    @classmethod
    def parse_json_string_to_list(cls, v: Any) -> list:
        """
        LEARNING NOTE: @field_validator
        ================================
        This decorator marks a method as a validator for specific fields.
        
        - First arg(s): field names to validate
        - mode='before': Run BEFORE type checking (so we can transform data)
        - @classmethod: Required because validators are called on the class
        
        The API returns lists as JSON strings like '["Yes", "No"]'
        We need to parse these into actual Python lists.
        """
        if v is None:
            return []
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        if isinstance(v, list):
            return v
        return []
    
    @field_validator('volume', 'volume_24hr', 'liquidity', mode='before')
    @classmethod
    def convert_number_to_string(cls, v: Any) -> str:
        """
        Volume fields come as floats/ints but we store as strings
        for consistency. This validator normalizes them.
        """
        if v is None:
            return "0"
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, str):
            return v
        return "0"
    
    # -------------------------------------------------------------------------
    # PROPERTIES: Computed values (not stored, calculated on access)
    # -------------------------------------------------------------------------
    
    @property
    def market_id(self) -> str:
        """
        LEARNING NOTE: @property
        =========================
        Properties let you access computed values like attributes.
        Instead of: market.get_market_id()
        You write:   market.market_id
        
        This is Pythonic - it looks like data access but runs code.
        """
        return self.id or self.condition_id or self.slug or "unknown"
    
    @property
    def display_question(self) -> str:
        """Get the best available question text."""
        return self.question or self.title or "Unknown Market"
    
    @property
    def total_volume(self) -> str:
        """Get the best available volume figure."""
        if self.volume_24hr and self.volume_24hr != "0":
            return self.volume_24hr
        return self.volume


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