"""
Database models and connection management for Polygraph.
Uses SQLAlchemy with async support (aiosqlite for SQLite).
"""

from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, Index, create_engine
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func

from src.config import get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# =============================================================================
# Database Models
# =============================================================================

class MarketModel(Base):
    """
    Tracked Polymarket markets.
    Stores metadata and current state for each market we're monitoring.
    """
    __tablename__ = "markets"
    
    id = Column(String, primary_key=True)  # Polymarket market ID
    condition_id = Column(String, unique=True, index=True)
    question = Column(Text, nullable=False)
    slug = Column(String, index=True)
    outcomes = Column(JSON, default=["Yes", "No"])
    
    # Token IDs for YES/NO outcomes
    yes_token_id = Column(String, nullable=True)
    no_token_id = Column(String, nullable=True)
    
    # Current state
    yes_price = Column(Float, default=0.5)
    no_price = Column(Float, default=0.5)
    volume_24h = Column(Float, default=0.0)
    liquidity = Column(Float, default=0.0)
    
    # Metadata
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_tracked = Column(Boolean, default=True)  # Whether we're actively monitoring
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    price_snapshots = relationship("PriceSnapshotModel", back_populates="market")
    signals = relationship("SignalModel", back_populates="market")
    
    def __repr__(self):
        return f"<Market(id={self.id[:10]}..., question={self.question[:30]}...)>"


class PriceSnapshotModel(Base):
    """
    Historical price data.
    Captures point-in-time market state for trend analysis.
    """
    __tablename__ = "price_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(String, ForeignKey("markets.id"), nullable=False, index=True)
    
    # Prices
    timestamp = Column(DateTime, nullable=False, index=True)
    yes_price = Column(Float, nullable=False)
    no_price = Column(Float, nullable=False)
    
    # Volume & depth
    volume = Column(Float, default=0.0)  # Volume since last snapshot
    cumulative_volume = Column(Float, default=0.0)  # Running total
    bid_depth = Column(Float, default=0.0)
    ask_depth = Column(Float, default=0.0)
    
    # Relationship
    market = relationship("MarketModel", back_populates="price_snapshots")
    
    # Composite index for efficient time-series queries
    __table_args__ = (
        Index('ix_snapshots_market_time', 'market_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<PriceSnapshot(market={self.market_id[:10]}..., time={self.timestamp})>"


class SignalModel(Base):
    """
    Detected signals.
    Each row represents a detected anomaly or interesting pattern.
    """
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(String, ForeignKey("markets.id"), nullable=False, index=True)
    
    # Signal metadata
    signal_type = Column(String, nullable=False, index=True)
    # Types: 'volume_spike', 'price_divergence', 'orderbook_imbalance', 'cross_market'
    
    timestamp = Column(DateTime, nullable=False, index=True)
    score = Column(Float, nullable=False)  # 0-100 composite score
    
    # Signal details (flexible JSON for different signal types)
    details = Column(JSON, default={})
    
    # Snapshot at time of signal
    price_at_signal = Column(Float, nullable=False)
    volume_at_signal = Column(Float, default=0.0)
    
    # Tracking
    is_acknowledged = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)  # For social media posting
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    market = relationship("MarketModel", back_populates="signals")
    
    # Index for recent signals query
    __table_args__ = (
        Index('ix_signals_time_score', 'timestamp', 'score'),
    )
    
    def __repr__(self):
        return f"<Signal(type={self.signal_type}, score={self.score}, market={self.market_id[:10]}...)>"


# =============================================================================
# Database Connection Management
# =============================================================================

class DatabaseManager:
    """
    Manages database connections and sessions.
    
    Usage:
        db = DatabaseManager()
        await db.initialize()
        
        async with db.session() as session:
            # Do database operations
            pass
    """
    
    def __init__(self, database_url: str = None):
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self._engine = None
        self._session_factory = None
    
    async def initialize(self):
        """Create engine and tables."""
        self._engine = create_async_engine(
            self.database_url,
            echo=get_settings().debug,
        )
        
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create all tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self):
        """Close the engine."""
        if self._engine:
            await self._engine.dispose()
    
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async session."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# =============================================================================
# Global database instance
# =============================================================================

_db_manager: DatabaseManager = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database sessions.
    
    Usage in FastAPI:
        @app.get("/markets")
        async def get_markets(db: AsyncSession = Depends(get_db)):
            ...
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    
    async for session in _db_manager.session():
        yield session


async def initialize_database():
    """Initialize the database on startup."""
    global _db_manager
    _db_manager = DatabaseManager()
    await _db_manager.initialize()


async def close_database():
    """Close database connections on shutdown."""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
