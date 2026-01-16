"""
Configuration settings for Polygraph.
Uses pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API URLs
    polymarket_gamma_url: str = "https://gamma-api.polymarket.com"
    polymarket_clob_url: str = "https://clob.polymarket.com"
    polymarket_ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./polygraph.db"
    
    # Polling intervals (seconds)
    price_poll_interval: int = 60
    market_refresh_interval: int = 300  # 5 minutes
    
    # Signal detection thresholds
    volume_spike_threshold: float = 2.5  # standard deviations
    volume_minimum: float = 10000.0  # minimum $ volume for signal
    imbalance_threshold: float = 3.0  # bid/ask ratio
    imbalance_minimum: float = 5000.0  # minimum $ depth
    price_change_threshold: float = 0.05  # 5% price change
    
    # Limits
    max_tracked_markets: int = 50  # Start small
    
    # Environment
    debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
