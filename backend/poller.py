#!/usr/bin/env python3
"""
Polling Service for Polygraph

Continuously fetches market data from Polymarket and runs signal detection.
This is the "heartbeat" of the application.

Usage:
    python poller.py

LEARNING CALLOUT: Long-Running Services
=======================================
This script runs indefinitely (until you Ctrl+C). It's a common pattern for:
- Data pipelines that need continuous updates
- Background workers processing queues
- Monitoring services that check system health

The main loop follows this pattern:
    while True:
        do_work()
        sleep(interval)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, update
from src.ingestion.polymarket import PolymarketClient
from src.database import (
    DatabaseManager, 
    MarketModel, 
    PriceSnapshotModel,
    SignalModel,
)
from src.signals.detector import SignalDetector, SignalResult
from src.config import get_settings


class PollingService:
    """
    Main polling service that orchestrates data fetching and signal detection.
    
    LEARNING CALLOUT: Class-Based Services
    ======================================
    We use a class here instead of loose functions because:
    1. State management - we need to track db connection, settings, etc.
    2. Lifecycle - clear init/start/stop phases
    3. Testability - easier to mock and test
    4. Organization - related methods grouped together
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.db: Optional[DatabaseManager] = None
        self.running = False
        
        # Stats for logging
        self.polls_completed = 0
        self.signals_detected = 0
        self.errors_encountered = 0
    
    async def initialize(self):
        """Set up database connection."""
        self.db = DatabaseManager()
        await self.db.initialize()
        print("✅ Database connection established")
    
    async def shutdown(self):
        """Clean up resources."""
        if self.db:
            await self.db.close()
        print("✅ Database connection closed")
    
    async def poll_market_prices(self) -> int:
        """
        Fetch current prices for all tracked markets.
        
        LEARNING CALLOUT: Batch Operations
        ===================================
        Instead of making one API call per market (slow, rate-limit risky),
        we fetch the market list which includes current prices.
        This is a common optimization: batch reads when possible.
        
        Returns:
            Number of markets updated
        """
        updated = 0
        
        async with PolymarketClient() as client:
            # Fetch fresh market data from Polymarket
            markets = await client.get_markets(
                limit=self.settings.max_tracked_markets,
                order="volume"
            )
            
            async for session in self.db.session():
                for market in markets:
                    try:
                        # Get existing market from our DB
                        result = await session.execute(
                            select(MarketModel).where(
                                MarketModel.id == market.market_id
                            )
                        )
                        db_market = result.scalar_one_or_none()
                        
                        if not db_market:
                            # Market not in our DB, skip (or could add it)
                            continue
                        
                        # Parse new prices
                        yes_price = db_market.yes_price  # Default to existing
                        no_price = db_market.no_price
                        
                        if market.outcome_prices and len(market.outcome_prices) >= 2:
                            try:
                                yes_price = float(market.outcome_prices[0])
                                no_price = float(market.outcome_prices[1])
                            except (ValueError, IndexError):
                                pass
                        
                        new_volume = float(market.total_volume or 0)
                        
                        # Calculate volume delta since last snapshot
                        last_snapshot = await session.execute(
                            select(PriceSnapshotModel)
                            .where(PriceSnapshotModel.market_id == market.market_id)
                            .order_by(PriceSnapshotModel.timestamp.desc())
                            .limit(1)
                        )
                        last = last_snapshot.scalar_one_or_none()
                        
                        volume_delta = 0
                        if last:
                            volume_delta = max(0, new_volume - last.cumulative_volume)
                        
                        # Create new price snapshot
                        snapshot = PriceSnapshotModel(
                            market_id=market.market_id,
                            timestamp=datetime.utcnow(),
                            yes_price=yes_price,
                            no_price=no_price,
                            volume=volume_delta,
                            cumulative_volume=new_volume,
                        )
                        session.add(snapshot)
                        
                        # Update market's current state
                        db_market.yes_price = yes_price
                        db_market.no_price = no_price
                        db_market.volume_24h = new_volume
                        db_market.liquidity = float(market.liquidity or 0)
                        db_market.updated_at = datetime.utcnow()
                        
                        updated += 1
                        
                    except Exception as e:
                        print(f"   ⚠️  Error updating {market.market_id[:20]}: {e}")
                        self.errors_encountered += 1
                
                await session.commit()
        
        return updated
    
    async def run_signal_detection(self) -> int:
        """
        Run signal detection on all tracked markets.
        
        Returns:
            Number of signals detected
        """
        signals_found = 0
        
        async for session in self.db.session():
            # Get all tracked markets
            result = await session.execute(
                select(MarketModel).where(MarketModel.is_tracked == True)
            )
            markets = result.scalars().all()
            
            detector = SignalDetector(session)
            
            for market in markets:
                try:
                    # Get latest snapshot for current values
                    snapshot_result = await session.execute(
                        select(PriceSnapshotModel)
                        .where(PriceSnapshotModel.market_id == market.id)
                        .order_by(PriceSnapshotModel.timestamp.desc())
                        .limit(1)
                    )
                    latest = snapshot_result.scalar_one_or_none()
                    
                    if not latest:
                        continue
                    
                    # Run detection algorithms
                    signals = await detector.analyze_market(
                        market_id=market.id,
                        current_price=latest.yes_price,
                        current_volume=latest.volume,
                        bid_depth=latest.bid_depth,
                        ask_depth=latest.ask_depth,
                    )
                    
                    # Save any detected signals
                    for signal in signals:
                        if signal.detected and signal.score >= 30:  # Minimum threshold
                            await detector.save_signal(
                                market_id=market.id,
                                signal_result=signal,
                                price_at_signal=latest.yes_price,
                                volume_at_signal=latest.volume,
                            )
                            signals_found += 1
                            
                            print(f"   🚨 SIGNAL: {signal.signal_type} "
                                  f"(score: {signal.score:.0f}) "
                                  f"on {market.question[:40]}...")
                
                except Exception as e:
                    print(f"   ⚠️  Error detecting signals for {market.id[:20]}: {e}")
                    self.errors_encountered += 1
            
            await session.commit()
        
        return signals_found
    
    async def poll_once(self):
        """
        Execute one polling cycle: fetch data, detect signals.
        
        LEARNING CALLOUT: Single Responsibility
        =======================================
        This method does ONE thing: execute one poll cycle.
        The loop logic is separate (in run()). This makes it:
        - Easier to test (call poll_once() in tests)
        - Easier to debug (run one cycle manually)
        - Clearer to read
        """
        cycle_start = datetime.utcnow()
        
        print(f"\n{'─'*50}")
        print(f"🔄 Poll #{self.polls_completed + 1} starting at {cycle_start.strftime('%H:%M:%S')}")
        
        # Step 1: Fetch new price data
        print("   📡 Fetching market prices...")
        updated = await self.poll_market_prices()
        print(f"   ✅ Updated {updated} markets")
        
        # Step 2: Run signal detection
        print("   🔍 Running signal detection...")
        signals = await self.run_signal_detection()
        if signals > 0:
            print(f"   🚨 Detected {signals} new signal(s)!")
            self.signals_detected += signals
        else:
            print(f"   ✅ No new signals")
        
        self.polls_completed += 1
        
        elapsed = (datetime.utcnow() - cycle_start).total_seconds()
        print(f"   ⏱️  Cycle completed in {elapsed:.1f}s")
    
    async def run(self):
        """
        Main polling loop. Runs until interrupted.
        
        LEARNING CALLOUT: Graceful Shutdown
        ===================================
        We use a try/finally pattern to ensure cleanup happens
        even if the loop is interrupted (Ctrl+C) or crashes.
        """
        self.running = True
        interval = self.settings.price_poll_interval
        
        print(f"\n{'='*60}")
        print("POLYGRAPH POLLING SERVICE")
        print(f"{'='*60}")
        print(f"\n⚙️  Configuration:")
        print(f"   • Poll interval: {interval} seconds")
        print(f"   • Max markets: {self.settings.max_tracked_markets}")
        print(f"   • Volume spike threshold: {self.settings.volume_spike_threshold}σ")
        print(f"\n🚀 Starting polling loop (Ctrl+C to stop)...")
        
        try:
            while self.running:
                await self.poll_once()
                
                # Wait for next cycle
                print(f"\n   💤 Sleeping {interval}s until next poll...")
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            print("\n\n⚠️  Polling cancelled")
        finally:
            self.print_stats()
    
    def print_stats(self):
        """Print summary statistics."""
        print(f"\n{'='*60}")
        print("POLLING SESSION SUMMARY")
        print(f"{'='*60}")
        print(f"   • Polls completed: {self.polls_completed}")
        print(f"   • Signals detected: {self.signals_detected}")
        print(f"   • Errors encountered: {self.errors_encountered}")
        print(f"{'='*60}\n")


async def main():
    """Entry point for the polling service."""
    service = PollingService()
    
    try:
        await service.initialize()
        await service.run()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
    finally:
        await service.shutdown()


if __name__ == "__main__":
    """
    LEARNING CALLOUT: asyncio.run()
    ================================
    asyncio.run() is the standard way to run async code from sync context.
    It:
    1. Creates a new event loop
    2. Runs the coroutine until complete
    3. Closes the loop and cleans up
    
    You only call this ONCE at the top level - everything else uses 'await'.
    """
    asyncio.run(main())