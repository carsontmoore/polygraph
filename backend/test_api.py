#!/usr/bin/env python3
"""
Test script to validate Polymarket API connection and data shape.
Run this to ensure we can fetch real data before building more infrastructure.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.polymarket import PolymarketClient


async def test_gamma_api():
    """Test the Gamma API for market metadata."""
    print("\n" + "="*70)
    print("TESTING GAMMA API (Market Metadata)")
    print("="*70)
    
    async with PolymarketClient() as client:
        # Test 1: Fetch top markets by volume
        print("\n📊 Fetching top 5 markets by volume...")
        markets = await client.get_markets(limit=5, order="volume")
        
        if not markets:
            print("❌ No markets returned!")
            return False
        
        print(f"✅ Found {len(markets)} markets\n")
        
        for i, market in enumerate(markets, 1):
            print(f"  {i}. {market.question[:60]}...")
            print(f"     ID: {market.id[:20]}...")
            print(f"     Volume: ${float(market.volume):,.2f}")
            print(f"     Outcomes: {market.outcomes}")
            if market.outcome_prices:
                print(f"     Prices: {market.outcome_prices}")
            print()
        
        # Test 2: Search functionality
        print("🔍 Testing search for 'bitcoin'...")
        btc_markets = await client.search_markets("bitcoin", limit=3)
        print(f"✅ Found {len(btc_markets)} Bitcoin-related markets\n")
        
        for market in btc_markets:
            print(f"  - {market.question[:50]}...")
        
        return markets


async def test_clob_api(markets):
    """Test the CLOB API for orderbook data."""
    print("\n" + "="*70)
    print("TESTING CLOB API (Orderbook & Prices)")
    print("="*70)
    
    # We need a token_id to test the CLOB API
    # Let's try to get one from the market data
    # The Gamma API sometimes includes token info
    
    async with PolymarketClient() as client:
        # First, let's see what the raw market data looks like
        print("\n🔍 Examining raw market data structure...")
        
        response = await client.client.get(
            f"{client.settings.polymarket_gamma_url}/markets",
            params={"limit": 1, "active": "true"}
        )
        raw_data = response.json()
        
        if raw_data:
            first_market = raw_data[0] if isinstance(raw_data, list) else raw_data
            print(f"\n📋 Raw market keys: {list(first_market.keys())}")
            
            # Check for token IDs
            if 'tokens' in first_market:
                print(f"\n🎯 Found tokens field!")
                tokens = first_market['tokens']
                print(f"   Tokens: {json.dumps(tokens, indent=2)[:500]}")
                
                if tokens and len(tokens) > 0:
                    token_id = tokens[0].get('token_id')
                    if token_id:
                        print(f"\n📈 Testing orderbook for token: {token_id[:30]}...")
                        
                        orderbook = await client.get_orderbook(token_id)
                        if orderbook:
                            print(f"✅ Orderbook received!")
                            print(f"   Bids: {len(orderbook.bids)} levels")
                            print(f"   Asks: {len(orderbook.asks)} levels")
                            
                            if orderbook.bids:
                                print(f"   Best bid: {orderbook.bids[0].price} @ {orderbook.bids[0].size}")
                            if orderbook.asks:
                                print(f"   Best ask: {orderbook.asks[0].price} @ {orderbook.asks[0].size}")
                            
                            # Calculate depth
                            bid_depth, ask_depth = client.calculate_orderbook_depth(orderbook)
                            print(f"   Bid depth: ${bid_depth:,.2f}")
                            print(f"   Ask depth: ${ask_depth:,.2f}")
                            
                            imbalance = client.calculate_imbalance_ratio(orderbook)
                            print(f"   Imbalance ratio: {imbalance:.2f}")
                        else:
                            print("❌ No orderbook data returned")
                        
                        # Test price endpoint
                        print(f"\n💰 Testing price endpoint...")
                        price = await client.get_price(token_id, "BUY")
                        if price:
                            print(f"✅ Price (BUY): {price}")
                        
                        midpoint = await client.get_midpoint(token_id)
                        if midpoint:
                            print(f"✅ Midpoint: {midpoint}")
            else:
                print("⚠️ No tokens field in market data - may need different approach")
                print(f"   Available fields: {list(first_market.keys())}")


async def test_data_for_signals():
    """Fetch data specifically useful for signal detection."""
    print("\n" + "="*70)
    print("FETCHING DATA FOR SIGNAL ANALYSIS")
    print("="*70)
    
    async with PolymarketClient() as client:
        # Get markets with high volume (most likely to have interesting signals)
        markets = await client.get_markets(limit=10, order="volume")
        
        print(f"\n📊 Top 10 markets by volume:\n")
        print(f"{'#':<3} {'Volume':>15} {'Liquidity':>12} Question")
        print("-" * 80)
        
        for i, market in enumerate(markets, 1):
            vol = float(market.volume)
            liq = float(market.liquidity) if market.liquidity else 0
            question = market.question[:45] + "..." if len(market.question) > 45 else market.question
            print(f"{i:<3} ${vol:>14,.0f} ${liq:>11,.0f} {question}")
        
        # Save sample data for offline analysis
        print("\n💾 Saving sample data to sample_markets.json...")
        
        sample_data = []
        for market in markets:
            sample_data.append({
                "id": market.id,
                "condition_id": market.condition_id,
                "question": market.question,
                "slug": market.slug,
                "outcomes": market.outcomes,
                "outcome_prices": market.outcome_prices,
                "volume": market.volume,
                "liquidity": market.liquidity,
            })
        
        with open("sample_markets.json", "w") as f:
            json.dump(sample_data, f, indent=2)
        
        print("✅ Sample data saved!")
        
        return markets


async def main():
    """Run all tests."""
    print("\n🚀 POLYGRAPH API VALIDATION TEST")
    print("=" * 70)
    print("Testing connection to Polymarket APIs...")
    
    try:
        # Test Gamma API
        markets = await test_gamma_api()
        
        if markets:
            # Test CLOB API
            await test_clob_api(markets)
            
            # Fetch signal-relevant data
            await test_data_for_signals()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nNext steps:")
        print("1. Review sample_markets.json for data structure")
        print("2. Implement database schema")
        print("3. Build polling service")
        print("4. Implement signal detection")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
