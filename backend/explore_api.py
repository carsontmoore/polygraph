#!/usr/bin/env python3
"""
Polymarket API Explorer
-----------------------
Quick validation script to understand the data shape from Polymarket APIs.

APIs:
- Gamma API (https://gamma-api.polymarket.com): Market metadata, events
- CLOB API (https://clob.polymarket.com): Orderbook, prices, trades
"""

import httpx
import json
from datetime import datetime
from typing import Any

# API Base URLs
GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"


def pretty_print(title: str, data: Any, max_items: int = 3) -> None:
    """Print data in a readable format."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)
    
    if isinstance(data, list):
        print(f"Total items: {len(data)}")
        print(f"Showing first {min(max_items, len(data))} items:\n")
        for i, item in enumerate(data[:max_items]):
            print(f"--- Item {i+1} ---")
            print(json.dumps(item, indent=2, default=str)[:2000])  # Truncate long items
            print()
    elif isinstance(data, dict):
        print(json.dumps(data, indent=2, default=str)[:3000])
    else:
        print(data)


def explore_gamma_api() -> dict:
    """Explore the Gamma API for market metadata."""
    print("\n" + "="*60)
    print("  EXPLORING GAMMA API (Market Metadata)")
    print("="*60)
    
    results = {}
    
    with httpx.Client(timeout=30) as client:
        # Get events
        print("\n[1] Fetching events...")
        try:
            resp = client.get(f"{GAMMA_API}/events", params={"limit": 5, "active": True})
            resp.raise_for_status()
            events = resp.json()
            results['events'] = events
            pretty_print("Active Events", events)
        except Exception as e:
            print(f"Error fetching events: {e}")
        
        # Get markets
        print("\n[2] Fetching markets...")
        try:
            resp = client.get(f"{GAMMA_API}/markets", params={"limit": 5, "active": True})
            resp.raise_for_status()
            markets = resp.json()
            results['markets'] = markets
            pretty_print("Active Markets", markets)
        except Exception as e:
            print(f"Error fetching markets: {e}")
    
    return results


def explore_clob_api(token_id: str = None) -> dict:
    """Explore the CLOB API for orderbook and price data."""
    print("\n" + "="*60)
    print("  EXPLORING CLOB API (Orderbook & Prices)")
    print("="*60)
    
    results = {}
    
    with httpx.Client(timeout=30) as client:
        # Get simplified markets from CLOB
        print("\n[1] Fetching CLOB markets...")
        try:
            resp = client.get(f"{CLOB_API}/markets")
            resp.raise_for_status()
            markets = resp.json()
            results['clob_markets'] = markets
            
            # Show summary
            if isinstance(markets, list):
                print(f"Total CLOB markets: {len(markets)}")
                active_markets = [m for m in markets if m.get('active', False)]
                print(f"Active markets: {len(active_markets)}")
                
                # Get a sample token_id for further exploration
                if active_markets and not token_id:
                    sample = active_markets[0]
                    if 'tokens' in sample and sample['tokens']:
                        token_id = sample['tokens'][0].get('token_id')
                        print(f"\nUsing sample token_id: {token_id}")
                
                pretty_print("Sample CLOB Markets", active_markets[:2])
        except Exception as e:
            print(f"Error fetching CLOB markets: {e}")
        
        # Get orderbook for a specific token
        if token_id:
            print(f"\n[2] Fetching orderbook for token: {token_id[:20]}...")
            try:
                resp = client.get(f"{CLOB_API}/book", params={"token_id": token_id})
                resp.raise_for_status()
                book = resp.json()
                results['orderbook'] = book
                pretty_print("Orderbook", book)
            except Exception as e:
                print(f"Error fetching orderbook: {e}")
            
            # Get price
            print(f"\n[3] Fetching price for token...")
            try:
                resp = client.get(f"{CLOB_API}/price", params={"token_id": token_id, "side": "BUY"})
                resp.raise_for_status()
                price = resp.json()
                results['price'] = price
                pretty_print("Price (BUY side)", price)
            except Exception as e:
                print(f"Error fetching price: {e}")
            
            # Get midpoint
            print(f"\n[4] Fetching midpoint...")
            try:
                resp = client.get(f"{CLOB_API}/midpoint", params={"token_id": token_id})
                resp.raise_for_status()
                midpoint = resp.json()
                results['midpoint'] = midpoint
                pretty_print("Midpoint", midpoint)
            except Exception as e:
                print(f"Error fetching midpoint: {e}")
    
    return results


def find_high_volume_markets(limit: int = 10) -> list:
    """Find the most active markets by volume."""
    print("\n" + "="*60)
    print("  FINDING HIGH-VOLUME MARKETS")
    print("="*60)
    
    with httpx.Client(timeout=30) as client:
        try:
            # Gamma API often has volume info
            resp = client.get(
                f"{GAMMA_API}/markets",
                params={"limit": 100, "active": True, "closed": False}
            )
            resp.raise_for_status()
            markets = resp.json()
            
            # Sort by volume if available
            markets_with_volume = []
            for m in markets:
                volume = m.get('volume', 0) or m.get('volumeNum', 0) or 0
                if isinstance(volume, str):
                    try:
                        volume = float(volume.replace(',', ''))
                    except:
                        volume = 0
                markets_with_volume.append({
                    'question': m.get('question', 'Unknown'),
                    'condition_id': m.get('conditionId', m.get('condition_id', '')),
                    'volume': volume,
                    'category': m.get('category', m.get('groupItemTitle', 'Unknown')),
                    'end_date': m.get('endDate', m.get('end_date_iso', '')),
                })
            
            # Sort by volume descending
            sorted_markets = sorted(markets_with_volume, key=lambda x: x['volume'], reverse=True)
            top_markets = sorted_markets[:limit]
            
            print(f"\nTop {limit} markets by volume:")
            for i, m in enumerate(top_markets, 1):
                vol_str = f"${m['volume']:,.0f}" if m['volume'] else "N/A"
                print(f"{i}. [{m['category']}] {m['question'][:60]}...")
                print(f"   Volume: {vol_str}")
            
            return top_markets
            
        except Exception as e:
            print(f"Error finding high volume markets: {e}")
            return []


def main():
    """Run the API exploration."""
    print("\n" + "#"*60)
    print("#  POLYMARKET API EXPLORATION")
    print(f"#  {datetime.now().isoformat()}")
    print("#"*60)
    
    # Explore Gamma API
    gamma_results = explore_gamma_api()
    
    # Explore CLOB API
    clob_results = explore_clob_api()
    
    # Find high volume markets for our initial tracking list
    high_volume = find_high_volume_markets(10)
    
    # Summary
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    print(f"""
API Access: {'✓ Working' if gamma_results or clob_results else '✗ Failed'}

Gamma API:
  - Events endpoint: {'✓' if gamma_results.get('events') else '✗'}
  - Markets endpoint: {'✓' if gamma_results.get('markets') else '✗'}

CLOB API:
  - Markets endpoint: {'✓' if clob_results.get('clob_markets') else '✗'}
  - Orderbook endpoint: {'✓' if clob_results.get('orderbook') else '✗'}
  - Price endpoint: {'✓' if clob_results.get('price') else '✗'}
  - Midpoint endpoint: {'✓' if clob_results.get('midpoint') else '✗'}

High Volume Markets Found: {len(high_volume)}
""")
    
    return {
        'gamma': gamma_results,
        'clob': clob_results,
        'high_volume_markets': high_volume
    }


if __name__ == "__main__":
    results = main()
