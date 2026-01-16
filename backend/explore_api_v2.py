#!/usr/bin/env python3
"""
Polymarket API Explorer v2
--------------------------
With browser-like headers to handle Cloudflare protection.
"""

import httpx
import json
from datetime import datetime
from typing import Any, Optional

# API Base URLs
GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"

# Browser-like headers to avoid Cloudflare blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://polymarket.com",
    "Referer": "https://polymarket.com/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}


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
            print(json.dumps(item, indent=2, default=str)[:2000])
            print()
    elif isinstance(data, dict):
        print(json.dumps(data, indent=2, default=str)[:3000])
    else:
        print(data)


def test_endpoint(client: httpx.Client, name: str, url: str, params: dict = None) -> Optional[Any]:
    """Test a single endpoint and return the result."""
    print(f"\n[Testing] {name}")
    print(f"  URL: {url}")
    if params:
        print(f"  Params: {params}")
    
    try:
        resp = client.get(url, params=params)
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"  ✓ Success - Got {type(data).__name__}")
            if isinstance(data, list):
                print(f"    Items: {len(data)}")
            return data
        elif resp.status_code == 403:
            print(f"  ✗ 403 Forbidden - Likely geo-blocked or Cloudflare challenge")
            # Check if it's HTML (Cloudflare page)
            if 'text/html' in resp.headers.get('content-type', ''):
                print(f"    (Received HTML challenge page)")
        else:
            print(f"  ✗ Error: {resp.text[:200]}")
        return None
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return None


def explore_apis():
    """Systematically explore all available endpoints."""
    print("\n" + "#"*60)
    print("#  POLYMARKET API EXPLORATION v2")
    print(f"#  {datetime.now().isoformat()}")
    print("#  (With browser-like headers)")
    print("#"*60)
    
    results = {}
    
    with httpx.Client(timeout=30, headers=HEADERS, follow_redirects=True) as client:
        
        # ===== GAMMA API TESTS =====
        print("\n" + "="*60)
        print("  GAMMA API (gamma-api.polymarket.com)")
        print("="*60)
        
        # Events endpoint
        results['gamma_events'] = test_endpoint(
            client, "Events (active)", 
            f"{GAMMA_API}/events",
            {"limit": 5, "active": "true", "closed": "false"}
        )
        
        # Markets endpoint
        results['gamma_markets'] = test_endpoint(
            client, "Markets (active)",
            f"{GAMMA_API}/markets", 
            {"limit": 5, "active": "true", "closed": "false"}
        )
        
        # Try without params
        results['gamma_markets_simple'] = test_endpoint(
            client, "Markets (no params)",
            f"{GAMMA_API}/markets"
        )
        
        # ===== CLOB API TESTS =====
        print("\n" + "="*60)
        print("  CLOB API (clob.polymarket.com)")
        print("="*60)
        
        # Markets endpoint
        results['clob_markets'] = test_endpoint(
            client, "CLOB Markets",
            f"{CLOB_API}/markets"
        )
        
        # Simplified markets
        results['clob_simplified'] = test_endpoint(
            client, "CLOB Simplified Markets",
            f"{CLOB_API}/simplified-markets"
        )
        
        # If we got markets, try to get orderbook for one
        token_id = None
        if results.get('clob_markets') and isinstance(results['clob_markets'], list):
            for m in results['clob_markets']:
                if m.get('tokens'):
                    token_id = m['tokens'][0].get('token_id')
                    break
        
        if token_id:
            results['clob_book'] = test_endpoint(
                client, f"Orderbook (token: {token_id[:20]}...)",
                f"{CLOB_API}/book",
                {"token_id": token_id}
            )
            
            results['clob_price'] = test_endpoint(
                client, "Price (BUY)",
                f"{CLOB_API}/price",
                {"token_id": token_id, "side": "BUY"}
            )
            
            results['clob_midpoint'] = test_endpoint(
                client, "Midpoint",
                f"{CLOB_API}/midpoint",
                {"token_id": token_id}
            )
        
        # ===== ALTERNATIVE: Direct Polymarket.com endpoints =====
        print("\n" + "="*60)
        print("  ALTERNATIVE ENDPOINTS")
        print("="*60)
        
        # Try the main polymarket.com API
        results['pm_markets'] = test_endpoint(
            client, "polymarket.com/api/markets",
            "https://polymarket.com/api/markets"
        )
        
        # Strapi endpoint (sometimes used)
        results['strapi'] = test_endpoint(
            client, "strapi-matic.poly.market",
            "https://strapi-matic.poly.market/markets",
            {"_limit": 5, "active": "true"}
        )
    
    # ===== SUMMARY =====
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    
    working = []
    blocked = []
    
    for name, data in results.items():
        if data is not None:
            working.append(name)
        else:
            blocked.append(name)
    
    print(f"\n✓ Working endpoints ({len(working)}):")
    for name in working:
        print(f"  - {name}")
    
    print(f"\n✗ Blocked/Failed endpoints ({len(blocked)}):")
    for name in blocked:
        print(f"  - {name}")
    
    # Show sample data from first working endpoint
    for name in working:
        data = results[name]
        if data:
            pretty_print(f"Sample data from: {name}", data, max_items=2)
            break
    
    return results


if __name__ == "__main__":
    results = explore_apis()
