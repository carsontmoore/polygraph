#!/usr/bin/env python3
"""
Seed Script for Polygraph

Fetches live market data from Polymarket and populates the local database.
Run this to see real data in the UI.

Usage:
    python seed_data.py

LEARNING CALLOUT: Script vs Module
==================================
This file is a "script" - meant to be run directly (python seed_data.py).
It's not a "module" meant to be imported by other code.

The `if __name__ == "__main__":` block at the bottom ensures the code
only runs when executed directly, not when imported.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from src.ingestion.polymarket import PolymarketClient
from src.database import DatabaseManager, MarketModel, PriceSnapshotModel
from src.config import get_settings


async def seed_markets(num_markets: int = 20) -> int:
    """
    Fetch top markets from Polymarket and store in database.
    
    LEARNING CALLOUT: async/await
    =============================
    - 'async def' defines a coroutine (async function)
    - 'await' pauses execution until the async operation completes
    - This lets us do I/O (API calls, DB writes) without blocking
    
    Args:
        num_markets: Number of markets to fetch
        
    Returns:
        Number of markets successfully stored
    """
    settings = get_settings()
    db = DatabaseManager()
    await db.initialize()
    
    print(f"\n{'='*60}")
    print("POLYGRAPH DATA SEEDER")
    print(f"{'='*60}")
    print(f"\n📡 Fetching top {num_markets} markets from Polymarket...\n")
    
    stored_count = 0
    
    async with PolymarketClient() as client:
        # Fetch markets sorted by volume
        markets = await client.get_markets(limit=num_markets, order="volume")
        
        print(f"✅ Fetched {len(markets)} markets from API\n")
        
        # Get a database session
        async for session in db.session():
            for market in markets:
                try:
                    # Check if market already exists
                    existing = await session.execute(
                        select(MarketModel).where(MarketModel.id == market.market_id)
                    )
                    if existing.scalar_one_or_none():
                        print(f"   ⏭️  Skipping (exists): {market.display_question[:50]}...")
                        continue
                    
                    # Parse prices from outcome_prices list
                    yes_price = 0.5
                    no_price = 0.5
                    if market.outcome_prices and len(market.outcome_prices) >= 2:
                        try:
                            yes_price = float(market.outcome_prices[0])
                            no_price = float(market.outcome_prices[1])
                        except (ValueError, IndexError):
                            pass
                    
                    # Extract token IDs
                    yes_token_id = None
                    no_token_id = None
                    if market.clob_token_ids and len(market.clob_token_ids) >= 2:
                        yes_token_id = market.clob_token_ids[0]
                        no_token_id = market.clob_token_ids[1]
                    
                    # Create market record
                    db_market = MarketModel(
                        id=market.market_id,
                        condition_id=market.condition_id or market.market_id,
                        question=market.display_question,
                        slug=market.slug or "",
                        outcomes=market.outcomes or ["Yes", "No"],
                        yes_token_id=yes_token_id,
                        no_token_id=no_token_id,
                        yes_price=yes_price,
                        no_price=no_price,
                        volume_24h=float(market.total_volume or 0),
                        liquidity=float(market.liquidity or 0),
                        is_active=market.active,
                        is_tracked=True,
                    )
                    
                    session.add(db_market)
                    
                    # Also create initial price snapshot
                    snapshot = PriceSnapshotModel(
                        market_id=market.market_id,
                        timestamp=datetime.utcnow(),
                        yes_price=yes_price,
                        no_price=no_price,
                        volume=float(market.total_volume or 0),
                        cumulative_volume=float(market.total_volume or 0),
                    )
                    session.add(snapshot)
                    
                    stored_count += 1
                    print(f"   ✅ Stored: {market.display_question[:50]}...")
                    
                except Exception as e:
                    print(f"   ❌ Error storing market: {e}")
                    continue
            
            # Commit all changes
            await session.commit()
    
    await db.close()
    
    return stored_count


async def print_summary():
    """Print summary of what's in the database."""
    db = DatabaseManager()
    await db.initialize()
    
    async for session in db.session():
        # Count markets
        result = await session.execute(select(MarketModel))
        markets = result.scalars().all()
        
        print(f"\n{'='*60}")
        print("DATABASE SUMMARY")
        print(f"{'='*60}")
        print(f"\n📊 Total markets in database: {len(markets)}")
        
        if markets:
            print(f"\n{'#':<3} {'Price':>8} {'Volume':>12} Question")
            print("-" * 70)
            
            # Sort by volume for display
            sorted_markets = sorted(markets, key=lambda m: m.volume_24h, reverse=True)
            
            for i, market in enumerate(sorted_markets[:10], 1):
                question = market.question[:42] + "..." if len(market.question) > 42 else market.question
                print(f"{i:<3} {market.yes_price:>7.1%} ${market.volume_24h:>10,.0f} {question}")
    
    await db.close()


async def main():
    """Main entry point."""
    print("\n🌱 Starting Polygraph data seeder...\n")
    
    # Seed the database
    stored = await seed_markets(num_markets=25)
    
    print(f"\n✅ Successfully stored {stored} new markets")
    
    # Print summary
    await print_summary()
    
    print(f"\n{'='*60}")
    print("🎉 SEEDING COMPLETE!")
    print(f"{'='*60}")
    print("\nRefresh http://localhost:3000 to see the data in the UI")
    print("")


if __name__ == "__main__":
    """
    LEARNING CALLOUT: if __name__ == "__main__"
    ============================================
    When Python runs a file directly, it sets __name__ to "__main__".
    When a file is imported, __name__ is set to the module name.
    
    This pattern lets you:
    - Run the file as a script: python seed_data.py (runs main())
    - Import it as a module: from seed_data import seed_markets (doesn't run main())
    """
    asyncio.run(main())