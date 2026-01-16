#!/usr/bin/env python3
"""
Mock Data Generator for Polygraph
----------------------------------
Generates realistic Polymarket-like data for frontend development
while we resolve API access issues.

This allows us to:
1. Build the full frontend against realistic data shapes
2. Test signal detection algorithms
3. Design the database schema
4. Move quickly without being blocked by API access
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import math


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Token:
    """Represents a YES or NO outcome token."""
    token_id: str
    outcome: str  # "Yes" or "No"
    price: float  # 0.0 to 1.0


@dataclass
class Market:
    """Represents a prediction market."""
    condition_id: str
    question: str
    description: str
    category: str
    end_date: str
    image_url: str
    volume_24h: float
    volume_total: float
    liquidity: float
    tokens: List[Dict]
    active: bool
    closed: bool
    created_at: str


@dataclass
class PricePoint:
    """A single price observation."""
    timestamp: str
    price: float
    volume: float


@dataclass
class Signal:
    """A detected trading signal."""
    id: str
    type: str  # VOLUME_SPIKE, PRICE_DIVERGENCE, WHALE_ACTIVITY, etc.
    market_id: str
    market_question: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    timestamp: str
    summary: str
    metadata: Dict[str, Any]


# =============================================================================
# SAMPLE DATA
# =============================================================================

SAMPLE_MARKETS = [
    {
        "question": "Will Bitcoin exceed $150,000 by July 2026?",
        "category": "Crypto",
        "description": "This market will resolve to 'Yes' if the price of Bitcoin (BTC) exceeds $150,000 USD at any point before July 1, 2026.",
        "days_until_end": 165,
        "base_yes_price": 0.42,
    },
    {
        "question": "Will the Fed cut rates in Q1 2026?",
        "category": "Economics",
        "description": "Resolves 'Yes' if the Federal Reserve announces a rate cut during Q1 2026.",
        "days_until_end": 74,
        "base_yes_price": 0.68,
    },
    {
        "question": "Will Tesla stock close above $500 by March 2026?",
        "category": "Stocks",
        "description": "Resolves 'Yes' if TSLA closes above $500 on any trading day before March 31, 2026.",
        "days_until_end": 74,
        "base_yes_price": 0.31,
    },
    {
        "question": "Super Bowl LX: Will the Chiefs win?",
        "category": "Sports",
        "description": "Resolves 'Yes' if the Kansas City Chiefs win Super Bowl LX.",
        "days_until_end": 25,
        "base_yes_price": 0.28,
    },
    {
        "question": "Will GPT-5 be released before July 2026?",
        "category": "Tech",
        "description": "Resolves 'Yes' if OpenAI publicly releases GPT-5 before July 1, 2026.",
        "days_until_end": 165,
        "base_yes_price": 0.55,
    },
    {
        "question": "Will there be a US government shutdown in 2026?",
        "category": "Politics",
        "description": "Resolves 'Yes' if the US federal government experiences a shutdown of any duration in 2026.",
        "days_until_end": 349,
        "base_yes_price": 0.62,
    },
    {
        "question": "Will Ethereum flip Bitcoin in market cap by 2027?",
        "category": "Crypto",
        "description": "Resolves 'Yes' if Ethereum's market cap exceeds Bitcoin's at any point before January 1, 2027.",
        "days_until_end": 349,
        "base_yes_price": 0.15,
    },
    {
        "question": "Academy Awards 2026: Will an AI-generated film win Best Picture?",
        "category": "Entertainment",
        "description": "Resolves 'Yes' if a film with significant AI-generated content wins Best Picture at the 2026 Academy Awards.",
        "days_until_end": 55,
        "base_yes_price": 0.08,
    },
    {
        "question": "Will Apple release AR glasses in 2026?",
        "category": "Tech",
        "description": "Resolves 'Yes' if Apple releases consumer AR glasses (not Vision Pro) in 2026.",
        "days_until_end": 349,
        "base_yes_price": 0.35,
    },
    {
        "question": "NBA Finals 2026: Will the Celtics repeat?",
        "category": "Sports",
        "description": "Resolves 'Yes' if the Boston Celtics win the 2026 NBA Finals.",
        "days_until_end": 150,
        "base_yes_price": 0.22,
    },
]

CATEGORIES = ["Crypto", "Politics", "Sports", "Tech", "Economics", "Entertainment", "Stocks"]

SIGNAL_TYPES = [
    ("VOLUME_SPIKE", "Unusual trading volume detected"),
    ("PRICE_DIVERGENCE", "Price movement without volume confirmation"),
    ("WHALE_ACTIVITY", "Large position opened"),
    ("NEW_WALLET", "Significant trade from new wallet"),
    ("ORDERBOOK_IMBALANCE", "Bid/ask ratio shifted significantly"),
]


# =============================================================================
# GENERATORS
# =============================================================================

def generate_id(prefix: str = "") -> str:
    """Generate a random hex ID."""
    return f"{prefix}{''.join(random.choices('0123456789abcdef', k=32))}"


def generate_market(market_data: dict, index: int) -> Market:
    """Generate a mock market from template data."""
    now = datetime.utcnow()
    end_date = now + timedelta(days=market_data["days_until_end"])
    created_at = now - timedelta(days=random.randint(30, 180))
    
    yes_price = market_data["base_yes_price"] + random.uniform(-0.05, 0.05)
    yes_price = max(0.01, min(0.99, yes_price))
    no_price = round(1 - yes_price, 4)
    
    return Market(
        condition_id=generate_id("0x"),
        question=market_data["question"],
        description=market_data["description"],
        category=market_data["category"],
        end_date=end_date.isoformat() + "Z",
        image_url=f"https://polymarket-upload.s3.amazonaws.com/market_{index}.png",
        volume_24h=random.uniform(10000, 500000),
        volume_total=random.uniform(500000, 10000000),
        liquidity=random.uniform(50000, 1000000),
        tokens=[
            {"token_id": generate_id(), "outcome": "Yes", "price": round(yes_price, 4)},
            {"token_id": generate_id(), "outcome": "No", "price": round(no_price, 4)},
        ],
        active=True,
        closed=False,
        created_at=created_at.isoformat() + "Z",
    )


def generate_price_history(
    base_price: float,
    hours: int = 168,  # 1 week
    volatility: float = 0.02
) -> List[PricePoint]:
    """Generate realistic price history with random walk."""
    points = []
    current_price = base_price
    now = datetime.utcnow()
    
    for i in range(hours, 0, -1):
        timestamp = now - timedelta(hours=i)
        
        # Random walk with mean reversion
        change = random.gauss(0, volatility)
        mean_reversion = (base_price - current_price) * 0.01
        current_price += change + mean_reversion
        current_price = max(0.01, min(0.99, current_price))
        
        # Volume varies by time of day (higher during US market hours)
        hour_of_day = timestamp.hour
        base_volume = 5000
        if 14 <= hour_of_day <= 22:  # 9am-5pm EST
            base_volume *= 2.5
        volume = base_volume * random.uniform(0.5, 2.0)
        
        points.append(PricePoint(
            timestamp=timestamp.isoformat() + "Z",
            price=round(current_price, 4),
            volume=round(volume, 2)
        ))
    
    return points


def generate_signal(market: Market, hours_ago: int = 0) -> Signal:
    """Generate a mock trading signal."""
    signal_type, description = random.choice(SIGNAL_TYPES)
    timestamp = datetime.utcnow() - timedelta(hours=hours_ago)
    
    severity_weights = {"LOW": 0.4, "MEDIUM": 0.35, "HIGH": 0.2, "CRITICAL": 0.05}
    severity = random.choices(
        list(severity_weights.keys()),
        weights=list(severity_weights.values())
    )[0]
    
    # Generate type-specific metadata
    metadata = {}
    if signal_type == "VOLUME_SPIKE":
        multiplier = random.uniform(2.5, 8.0)
        metadata = {
            "current_volume": round(random.uniform(50000, 200000), 2),
            "baseline_volume": round(random.uniform(10000, 50000), 2),
            "multiplier": round(multiplier, 2),
        }
        summary = f"Trading volume {multiplier:.1f}x above 24h average"
    elif signal_type == "WHALE_ACTIVITY":
        size = random.uniform(50000, 500000)
        metadata = {
            "position_size": round(size, 2),
            "side": random.choice(["BUY", "SELL"]),
            "outcome": random.choice(["Yes", "No"]),
        }
        summary = f"${size:,.0f} {metadata['side']} position on {metadata['outcome']}"
    elif signal_type == "PRICE_DIVERGENCE":
        price_change = random.uniform(0.05, 0.15)
        metadata = {
            "price_change_pct": round(price_change * 100, 2),
            "volume_change_pct": round(random.uniform(-20, 20), 2),
            "direction": random.choice(["UP", "DOWN"]),
        }
        summary = f"Price moved {price_change*100:.1f}% {metadata['direction']} without volume confirmation"
    else:
        summary = description
        metadata = {"detected_at": timestamp.isoformat()}
    
    return Signal(
        id=generate_id("sig_"),
        type=signal_type,
        market_id=market.condition_id,
        market_question=market.question,
        severity=severity,
        timestamp=timestamp.isoformat() + "Z",
        summary=summary,
        metadata=metadata
    )


def generate_all_mock_data() -> Dict[str, Any]:
    """Generate a complete mock dataset."""
    print("Generating mock Polymarket data...")
    
    # Generate markets
    markets = [generate_market(data, i) for i, data in enumerate(SAMPLE_MARKETS)]
    print(f"  ✓ Generated {len(markets)} markets")
    
    # Generate price history for each market
    price_histories = {}
    for market in markets:
        yes_price = market.tokens[0]["price"]
        price_histories[market.condition_id] = [
            asdict(p) for p in generate_price_history(yes_price, hours=168)
        ]
    print(f"  ✓ Generated price history (168 hours each)")
    
    # Generate signals
    signals = []
    for _ in range(15):
        market = random.choice(markets)
        hours_ago = random.randint(0, 48)
        signals.append(asdict(generate_signal(market, hours_ago)))
    
    # Sort signals by timestamp (newest first)
    signals.sort(key=lambda x: x["timestamp"], reverse=True)
    print(f"  ✓ Generated {len(signals)} signals")
    
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "markets": [asdict(m) for m in markets],
        "price_histories": price_histories,
        "signals": signals,
    }


def save_mock_data(output_dir: str = "mock_data"):
    """Generate and save mock data to JSON files."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    data = generate_all_mock_data()
    
    # Save all data
    with open(output_path / "all_data.json", "w") as f:
        json.dump(data, f, indent=2)
    
    # Save individual files for easier consumption
    with open(output_path / "markets.json", "w") as f:
        json.dump(data["markets"], f, indent=2)
    
    with open(output_path / "signals.json", "w") as f:
        json.dump(data["signals"], f, indent=2)
    
    with open(output_path / "price_histories.json", "w") as f:
        json.dump(data["price_histories"], f, indent=2)
    
    print(f"\n✓ Mock data saved to {output_path}/")
    print(f"  - all_data.json")
    print(f"  - markets.json")
    print(f"  - signals.json")
    print(f"  - price_histories.json")
    
    return data


if __name__ == "__main__":
    data = save_mock_data()
    
    # Print sample
    print("\n" + "="*60)
    print("  SAMPLE DATA")
    print("="*60)
    
    print("\nSample Market:")
    print(json.dumps(data["markets"][0], indent=2))
    
    print("\nSample Signal:")
    print(json.dumps(data["signals"][0], indent=2))
