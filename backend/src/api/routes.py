"""
API routes for Polygraph.

Provides REST endpoints for:
- Market data and listings
- Signal feeds
- System stats
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db, MarketModel, PriceSnapshotModel, SignalModel
from src.models import (
    MarketSummary, SignalResponse, DashboardStats, Market, Signal
)


router = APIRouter()


# =============================================================================
# Market Endpoints
# =============================================================================

@router.get("/markets", response_model=list[MarketSummary])
async def list_markets(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    active_only: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
):
    """
    List tracked markets with summary info.
    
    Returns markets sorted by 24h volume, with recent signal counts.
    """
    # Base query for markets
    query = select(MarketModel)
    
    if active_only:
        query = query.where(
            MarketModel.is_active == True,
            MarketModel.is_tracked == True
        )
    
    query = query.order_by(desc(MarketModel.volume_24h)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    markets = result.scalars().all()
    
    # Get signal counts for each market (last 24h)
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    summaries = []
    for market in markets:
        # Count recent signals
        signal_query = select(func.count(SignalModel.id)).where(
            SignalModel.market_id == market.id,
            SignalModel.timestamp >= cutoff
        )
        signal_result = await db.execute(signal_query)
        signal_count = signal_result.scalar() or 0
        
        # Get most recent signal time
        last_signal_query = select(SignalModel.timestamp).where(
            SignalModel.market_id == market.id
        ).order_by(desc(SignalModel.timestamp)).limit(1)
        last_signal_result = await db.execute(last_signal_query)
        last_signal_row = last_signal_result.fetchone()
        
        summaries.append(MarketSummary(
            id=market.id,
            question=market.question,
            slug=market.slug,
            yes_price=market.yes_price,
            volume_24h=market.volume_24h,
            recent_signals=signal_count,
            last_signal_at=last_signal_row[0] if last_signal_row else None,
        ))
    
    return summaries


@router.get("/markets/{market_id}")
async def get_market(
    market_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed market information including price history.
    """
    # Fetch market
    query = select(MarketModel).where(MarketModel.id == market_id)
    result = await db.execute(query)
    market = result.scalar_one_or_none()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    # Fetch price history (last 7 days)
    cutoff = datetime.utcnow() - timedelta(days=7)
    history_query = select(PriceSnapshotModel).where(
        PriceSnapshotModel.market_id == market_id,
        PriceSnapshotModel.timestamp >= cutoff
    ).order_by(PriceSnapshotModel.timestamp)
    
    history_result = await db.execute(history_query)
    snapshots = history_result.scalars().all()
    
    # Fetch recent signals
    signals_query = select(SignalModel).where(
        SignalModel.market_id == market_id
    ).order_by(desc(SignalModel.timestamp)).limit(10)
    
    signals_result = await db.execute(signals_query)
    signals = signals_result.scalars().all()
    
    return {
        "market": {
            "id": market.id,
            "question": market.question,
            "slug": market.slug,
            "outcomes": market.outcomes,
            "yes_price": market.yes_price,
            "no_price": market.no_price,
            "volume_24h": market.volume_24h,
            "liquidity": market.liquidity,
            "end_date": market.end_date,
            "is_active": market.is_active,
            "updated_at": market.updated_at,
        },
        "price_history": [
            {
                "timestamp": s.timestamp,
                "yes_price": s.yes_price,
                "no_price": s.no_price,
                "volume": s.volume,
            }
            for s in snapshots
        ],
        "recent_signals": [
            {
                "id": s.id,
                "signal_type": s.signal_type,
                "timestamp": s.timestamp,
                "score": s.score,
                "details": s.details,
            }
            for s in signals
        ],
    }


# =============================================================================
# Signal Endpoints
# =============================================================================

@router.get("/signals", response_model=list[SignalResponse])
async def list_signals(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    min_score: float = Query(default=0.0, ge=0, le=100),
    signal_type: Optional[str] = Query(default=None),
    market_id: Optional[str] = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),  # Max 1 week
    db: AsyncSession = Depends(get_db),
):
    """
    List detected signals with filtering options.
    
    Signals are sorted by timestamp (newest first).
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    query = select(SignalModel).where(
        SignalModel.timestamp >= cutoff,
        SignalModel.score >= min_score
    )
    
    if signal_type:
        query = query.where(SignalModel.signal_type == signal_type)
    
    if market_id:
        query = query.where(SignalModel.market_id == market_id)
    
    query = query.order_by(desc(SignalModel.timestamp)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    signals = result.scalars().all()
    
    # Fetch market questions for response
    market_ids = list(set(s.market_id for s in signals))
    if market_ids:
        markets_query = select(MarketModel.id, MarketModel.question).where(
            MarketModel.id.in_(market_ids)
        )
        markets_result = await db.execute(markets_query)
        market_questions = {row[0]: row[1] for row in markets_result.fetchall()}
    else:
        market_questions = {}
    
    return [
        SignalResponse(
            id=s.id,
            market_id=s.market_id,
            market_question=market_questions.get(s.market_id, "Unknown"),
            signal_type=s.signal_type,
            timestamp=s.timestamp,
            score=s.score,
            details=s.details,
            price_at_signal=s.price_at_signal,
        )
        for s in signals
    ]


@router.get("/signals/top")
async def get_top_signals(
    limit: int = Query(default=10, le=50),
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """
    Get highest-scoring signals in the time period.
    
    Useful for highlighting the most significant market movements.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    query = select(SignalModel).where(
        SignalModel.timestamp >= cutoff
    ).order_by(desc(SignalModel.score)).limit(limit)
    
    result = await db.execute(query)
    signals = result.scalars().all()
    
    # Fetch market info
    market_ids = list(set(s.market_id for s in signals))
    if market_ids:
        markets_query = select(MarketModel).where(MarketModel.id.in_(market_ids))
        markets_result = await db.execute(markets_query)
        markets = {m.id: m for m in markets_result.scalars().all()}
    else:
        markets = {}
    
    return [
        {
            "signal": {
                "id": s.id,
                "signal_type": s.signal_type,
                "timestamp": s.timestamp,
                "score": s.score,
                "details": s.details,
                "price_at_signal": s.price_at_signal,
            },
            "market": {
                "id": s.market_id,
                "question": markets.get(s.market_id, MarketModel()).question,
                "yes_price": markets.get(s.market_id, MarketModel()).yes_price,
            } if s.market_id in markets else None
        }
        for s in signals
    ]


# =============================================================================
# Dashboard Endpoints
# =============================================================================

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get summary statistics for the dashboard.
    """
    # Count tracked markets
    markets_query = select(func.count(MarketModel.id)).where(
        MarketModel.is_tracked == True
    )
    markets_result = await db.execute(markets_query)
    total_markets = markets_result.scalar() or 0
    
    # Count signals in last 24h
    cutoff = datetime.utcnow() - timedelta(hours=24)
    signals_query = select(func.count(SignalModel.id)).where(
        SignalModel.timestamp >= cutoff
    )
    signals_result = await db.execute(signals_query)
    signals_24h = signals_result.scalar() or 0
    
    # Get highest scoring signal
    top_signal_query = select(SignalModel).where(
        SignalModel.timestamp >= cutoff
    ).order_by(desc(SignalModel.score)).limit(1)
    top_signal_result = await db.execute(top_signal_query)
    top_signal = top_signal_result.scalar_one_or_none()
    
    top_signal_response = None
    if top_signal:
        # Get market question
        market_query = select(MarketModel.question).where(
            MarketModel.id == top_signal.market_id
        )
        market_result = await db.execute(market_query)
        question = market_result.scalar() or "Unknown"
        
        top_signal_response = SignalResponse(
            id=top_signal.id,
            market_id=top_signal.market_id,
            market_question=question,
            signal_type=top_signal.signal_type,
            timestamp=top_signal.timestamp,
            score=top_signal.score,
            details=top_signal.details,
            price_at_signal=top_signal.price_at_signal,
        )
    
    # Get most active market (most signals)
    active_market_query = select(
        SignalModel.market_id,
        func.count(SignalModel.id).label('signal_count')
    ).where(
        SignalModel.timestamp >= cutoff
    ).group_by(
        SignalModel.market_id
    ).order_by(
        desc('signal_count')
    ).limit(1)
    
    active_result = await db.execute(active_market_query)
    active_row = active_result.fetchone()
    
    most_active = None
    if active_row:
        market_query = select(MarketModel).where(
            MarketModel.id == active_row[0]
        )
        market_result = await db.execute(market_query)
        market = market_result.scalar_one_or_none()
        
        if market:
            most_active = MarketSummary(
                id=market.id,
                question=market.question,
                slug=market.slug,
                yes_price=market.yes_price,
                volume_24h=market.volume_24h,
                recent_signals=active_row[1],
            )
    
    return DashboardStats(
        total_markets_tracked=total_markets,
        signals_24h=signals_24h,
        highest_score_signal=top_signal_response,
        most_active_market=most_active,
    )


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
    }
