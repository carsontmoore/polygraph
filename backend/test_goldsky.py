#!/usr/bin/env python3
"""
Polymarket Data via Goldsky GraphQL
-----------------------------------
Testing the subgraph endpoints hosted by Goldsky.

From Polymarket docs:
- Orders subgraph: https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/prod/gn
- PNL subgraph: https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/pnl-subgraph/0.0.14/gn
"""

import httpx
import json
from datetime import datetime

# Goldsky GraphQL endpoints (no Cloudflare protection!)
ORDERBOOK_SUBGRAPH = "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/prod/gn"
PNL_SUBGRAPH = "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/pnl-subgraph/0.0.14/gn"


def query_graphql(endpoint: str, query: str, variables: dict = None) -> dict:
    """Execute a GraphQL query."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    with httpx.Client(timeout=30) as client:
        resp = client.post(endpoint, json=payload)
        resp.raise_for_status()
        return resp.json()


def test_orderbook_subgraph():
    """Test the orderbook subgraph."""
    print("\n" + "="*60)
    print("  ORDERBOOK SUBGRAPH")
    print("="*60)
    
    # Query for recent orders
    query = """
    {
      orders(first: 5, orderBy: timestamp, orderDirection: desc) {
        id
        maker
        taker
        side
        price
        size
        timestamp
        status
        tokenId
        market {
          id
          condition {
            id
          }
        }
      }
    }
    """
    
    try:
        result = query_graphql(ORDERBOOK_SUBGRAPH, query)
        print("\n✓ Orders query successful!")
        print(f"  Found {len(result.get('data', {}).get('orders', []))} orders")
        print("\nSample data:")
        print(json.dumps(result, indent=2)[:2000])
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def test_pnl_subgraph():
    """Test the PNL subgraph."""
    print("\n" + "="*60)
    print("  PNL SUBGRAPH")
    print("="*60)
    
    # Query for user positions
    query = """
    {
      userPositions(first: 5, orderBy: lastUpdated, orderDirection: desc) {
        id
        user
        market
        outcome
        shares
        avgPrice
        realizedPnl
        lastUpdated
      }
    }
    """
    
    try:
        result = query_graphql(PNL_SUBGRAPH, query)
        print("\n✓ PNL query successful!")
        print(f"  Found {len(result.get('data', {}).get('userPositions', []))} positions")
        print("\nSample data:")
        print(json.dumps(result, indent=2)[:2000])
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def explore_schema(endpoint: str, name: str):
    """Fetch the GraphQL schema to understand available queries."""
    print(f"\n{'='*60}")
    print(f"  SCHEMA EXPLORATION: {name}")
    print("="*60)
    
    # Introspection query
    query = """
    {
      __schema {
        queryType {
          fields {
            name
            description
            args {
              name
              type {
                name
                kind
              }
            }
          }
        }
      }
    }
    """
    
    try:
        result = query_graphql(endpoint, query)
        fields = result.get('data', {}).get('__schema', {}).get('queryType', {}).get('fields', [])
        
        print(f"\nAvailable query types ({len(fields)}):")
        for field in fields[:20]:  # Show first 20
            args = [a['name'] for a in field.get('args', [])]
            print(f"  - {field['name']}: {', '.join(args[:5])}...")
        
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def get_market_data():
    """Try to get actual market data from the subgraph."""
    print("\n" + "="*60)
    print("  FETCHING MARKET DATA")
    print("="*60)
    
    # Try different queries to find market data
    queries = [
        # Markets
        ("markets", """
        {
          markets(first: 10, orderBy: timestamp, orderDirection: desc) {
            id
            timestamp
            condition {
              id
              questionId
            }
            fee
            collateralToken {
              id
              symbol
            }
          }
        }
        """),
        
        # Conditions (markets)
        ("conditions", """
        {
          conditions(first: 10, orderBy: timestamp, orderDirection: desc) {
            id
            questionId
            timestamp
            resolutionTimestamp
            payoutNumerators
            payoutDenominator
          }
        }
        """),
        
        # Recent trades
        ("trades", """
        {
          trades(first: 10, orderBy: timestamp, orderDirection: desc) {
            id
            maker
            taker
            side
            price
            size
            timestamp
            market {
              id
            }
          }
        }
        """),
        
        # Token positions
        ("tokenPositions", """
        {
          tokenPositions(first: 10, orderBy: shares, orderDirection: desc) {
            id
            token
            user
            shares
          }
        }
        """),
    ]
    
    results = {}
    for name, query in queries:
        print(f"\n[Testing] {name}...")
        try:
            result = query_graphql(ORDERBOOK_SUBGRAPH, query)
            data = result.get('data', {}).get(name, [])
            if data:
                print(f"  ✓ Found {len(data)} items")
                results[name] = data
            else:
                errors = result.get('errors', [])
                if errors:
                    print(f"  ✗ Error: {errors[0].get('message', 'Unknown')}")
                else:
                    print(f"  - No data found")
        except Exception as e:
            print(f"  ✗ Exception: {e}")
    
    return results


def main():
    """Run all tests."""
    print("\n" + "#"*60)
    print("#  POLYMARKET GOLDSKY SUBGRAPH EXPLORATION")
    print(f"#  {datetime.now().isoformat()}")
    print("#"*60)
    
    # Test basic connectivity
    orderbook_result = test_orderbook_subgraph()
    pnl_result = test_pnl_subgraph()
    
    # Explore available queries
    explore_schema(ORDERBOOK_SUBGRAPH, "Orderbook Subgraph")
    
    # Get actual market data
    market_data = get_market_data()
    
    # Summary
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    
    print(f"""
Goldsky Subgraph Access:
  - Orderbook subgraph: {'✓ Working' if orderbook_result else '✗ Failed'}
  - PNL subgraph: {'✓ Working' if pnl_result else '✗ Failed'}

Data found:
""")
    for name, data in market_data.items():
        print(f"  - {name}: {len(data)} items")
    
    return {
        'orderbook': orderbook_result,
        'pnl': pnl_result,
        'market_data': market_data
    }


if __name__ == "__main__":
    results = main()
