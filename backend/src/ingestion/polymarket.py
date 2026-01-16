"""
Polymarket API client for fetching market data.

This module handles all communication with Polymarket's APIs:
- Gamma API: Market metadata, events, search
- CLOB API: Orderbook, prices, trades
"""

import httpx
from typing import Optional
from datetime import datetime

from src.config import get_settings
from src.models import PolymarketMarket, Orderbook, OrderbookEntry


class PolymarketClient:
    """
    Client for interacting with Polymarket APIs.
    
    Usage:
        async with PolymarketClient() as client:
            markets = await client.get_markets(limit=10)
            orderbook = await client.get_orderbook(token_id)
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Polygraph/0.1"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._client
    
    # =========================================================================
    # Gamma API - Market Metadata
    # =========================================================================
    
    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
        closed: bool = False,
        order: str = "volume",  # volume, liquidity, created
        ascending: bool = False,
    ) -> list[PolymarketMarket]:
        """
        Fetch markets from Gamma API.
        
        Args:
            limit: Max markets to return (max 100)
            offset: Pagination offset
            active: Filter to active markets
            closed: Include closed markets
            order: Sort field
            ascending: Sort direction
            
        Returns:
            List of market objects
        """
        params = {
            "limit": min(limit, 100),
            "offset": offset,
            "active": str(active).lower(),
            "closed": str(closed).lower(),
            "order": order,
            "ascending": str(ascending).lower(),
        }
        
        response = await self.client.get(
            f"{self.settings.polymarket_gamma_url}/markets",
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Handle both list and paginated response formats
        markets_data = data if isinstance(data, list) else data.get("data", [])
        
        markets = []
        for m in markets_data:
            try:
                market = PolymarketMarket.model_validate(m)
                markets.append(market)
            except Exception as e:
                # Log but don't fail on individual market parse errors
                if self.settings.debug:
                    print(f"Failed to parse market: {e}")
                continue
        
        return markets
    
    async def get_market(self, market_id: str) -> Optional[PolymarketMarket]:
        """
        Fetch single market by ID.
        
        Args:
            market_id: The market's condition_id or slug
            
        Returns:
            Market object or None if not found
        """
        response = await self.client.get(
            f"{self.settings.polymarket_gamma_url}/markets/{market_id}"
        )
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        return PolymarketMarket.model_validate(response.json())
    
    async def search_markets(self, query: str, limit: int = 20) -> list[PolymarketMarket]:
        """
        Search markets by text query.
        
        Args:
            query: Search string
            limit: Max results
            
        Returns:
            List of matching markets
        """
        params = {"query": query, "limit": limit}
        
        response = await self.client.get(
            f"{self.settings.polymarket_gamma_url}/markets",
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        markets_data = data if isinstance(data, list) else data.get("data", [])
        
        return [PolymarketMarket.model_validate(m) for m in markets_data]
    
    # =========================================================================
    # CLOB API - Orderbook & Prices
    # =========================================================================
    
    async def get_orderbook(self, token_id: str) -> Optional[Orderbook]:
        """
        Get orderbook for a token.
        
        Args:
            token_id: The token's asset_id
            
        Returns:
            Orderbook snapshot or None if not found
        """
        params = {"token_id": token_id}
        
        response = await self.client.get(
            f"{self.settings.polymarket_clob_url}/book",
            params=params
        )
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        return Orderbook.model_validate(response.json())
    
    async def get_price(self, token_id: str, side: str = "BUY") -> Optional[float]:
        """
        Get current price for a token.
        
        Args:
            token_id: The token's asset_id
            side: BUY or SELL
            
        Returns:
            Price as float or None
        """
        params = {"token_id": token_id, "side": side}
        
        response = await self.client.get(
            f"{self.settings.polymarket_clob_url}/price",
            params=params
        )
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        data = response.json()
        
        return float(data.get("price", 0))
    
    async def get_midpoint(self, token_id: str) -> Optional[float]:
        """
        Get midpoint price for a token.
        
        Args:
            token_id: The token's asset_id
            
        Returns:
            Midpoint price as float or None
        """
        params = {"token_id": token_id}
        
        response = await self.client.get(
            f"{self.settings.polymarket_clob_url}/midpoint",
            params=params
        )
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        data = response.json()
        
        return float(data.get("mid", 0))
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def calculate_orderbook_depth(
        self, 
        orderbook: Orderbook, 
        levels: int = 10
    ) -> tuple[float, float]:
        """
        Calculate total bid and ask depth in USD.
        
        Args:
            orderbook: Orderbook snapshot
            levels: Number of levels to include
            
        Returns:
            Tuple of (bid_depth, ask_depth) in USD
        """
        bid_depth = sum(
            float(entry.price) * float(entry.size) 
            for entry in orderbook.bids[:levels]
        )
        ask_depth = sum(
            float(entry.price) * float(entry.size) 
            for entry in orderbook.asks[:levels]
        )
        
        return bid_depth, ask_depth
    
    def calculate_imbalance_ratio(
        self, 
        orderbook: Orderbook, 
        levels: int = 10
    ) -> float:
        """
        Calculate orderbook imbalance ratio.
        
        Args:
            orderbook: Orderbook snapshot
            levels: Number of levels to include
            
        Returns:
            Ratio of larger side to smaller side (>= 1.0)
        """
        bid_depth, ask_depth = self.calculate_orderbook_depth(orderbook, levels)
        
        if bid_depth == 0 and ask_depth == 0:
            return 1.0
        if bid_depth == 0 or ask_depth == 0:
            return float('inf')
            
        return max(bid_depth, ask_depth) / min(bid_depth, ask_depth)


# =============================================================================
# Convenience function for quick testing
# =============================================================================

async def test_client():
    """Quick test of the client."""
    async with PolymarketClient() as client:
        print("Fetching top markets by volume...")
        markets = await client.get_markets(limit=5, order="volume")
        
        for market in markets:
            print(f"\n{'='*60}")
            print(f"Question: {market.question}")
            print(f"ID: {market.id}")
            print(f"Volume: ${float(market.volume):,.2f}")
            print(f"Outcomes: {market.outcomes}")
            print(f"Prices: {market.outcome_prices}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_client())
