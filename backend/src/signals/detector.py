"""
Signal detection engine for Polygraph.

This module contains the core algorithms for detecting interesting
patterns in prediction market data.
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
import numpy as np
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import PriceSnapshotModel, SignalModel, MarketModel
from src.models import Signal


@dataclass
class SignalResult:
    """Result from signal detection."""
    detected: bool
    signal_type: str
    score: float
    details: dict


class SignalDetector:
    """
    Main signal detection engine.
    
    Analyzes market data to detect:
    - Volume spikes (unusual trading activity)
    - Orderbook imbalances (asymmetric liquidity)
    - Price divergences (price moves without volume, or vice versa)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
    
    async def analyze_market(
        self, 
        market_id: str,
        current_price: float,
        current_volume: float,
        bid_depth: float = 0.0,
        ask_depth: float = 0.0,
    ) -> list[SignalResult]:
        """
        Run all signal detection algorithms on a market.
        
        Args:
            market_id: The market to analyze
            current_price: Current YES price
            current_volume: Recent volume
            bid_depth: Total bid liquidity
            ask_depth: Total ask liquidity
            
        Returns:
            List of detected signals (may be empty)
        """
        signals = []
        
        # Check for volume spike
        volume_signal = await self.detect_volume_spike(
            market_id, current_volume
        )
        if volume_signal.detected:
            signals.append(volume_signal)
        
        # Check for orderbook imbalance
        if bid_depth > 0 or ask_depth > 0:
            imbalance_signal = await self.detect_orderbook_imbalance(
                market_id, bid_depth, ask_depth
            )
            if imbalance_signal.detected:
                signals.append(imbalance_signal)
        
        # Check for price divergence
        divergence_signal = await self.detect_price_divergence(
            market_id, current_price, current_volume
        )
        if divergence_signal.detected:
            signals.append(divergence_signal)
        
        return signals
    
    async def detect_volume_spike(
        self, 
        market_id: str, 
        current_volume: float
    ) -> SignalResult:
        """
        Detect unusual volume activity.
        
        A volume spike occurs when current volume exceeds N standard
        deviations from the rolling average.
        
        Args:
            market_id: Market to analyze
            current_volume: Current period volume
            
        Returns:
            SignalResult with detection status and details
        """
        # Get historical volume data (last 24 hours)
        lookback = datetime.utcnow() - timedelta(hours=24)
        
        query = select(PriceSnapshotModel.volume).where(
            PriceSnapshotModel.market_id == market_id,
            PriceSnapshotModel.timestamp >= lookback
        ).order_by(PriceSnapshotModel.timestamp.desc())
        
        result = await self.session.execute(query)
        volumes = [row[0] for row in result.fetchall() if row[0] is not None]
        
        # Need minimum data points for statistical analysis
        if len(volumes) < 10:
            return SignalResult(
                detected=False,
                signal_type="volume_spike",
                score=0.0,
                details={"reason": "insufficient_data", "data_points": len(volumes)}
            )
        
        # Calculate statistics
        volumes_array = np.array(volumes)
        mean_volume = np.mean(volumes_array)
        std_volume = np.std(volumes_array)
        
        # Avoid division by zero
        if std_volume == 0:
            z_score = 0.0
        else:
            z_score = (current_volume - mean_volume) / std_volume
        
        # Check thresholds
        threshold = self.settings.volume_spike_threshold
        min_volume = self.settings.volume_minimum
        
        is_spike = (
            z_score > threshold and 
            current_volume > min_volume
        )
        
        # Calculate score (0-100)
        # Score increases with z-score, capped at 40 points for volume component
        if is_spike:
            # Normalize z-score to 0-40 range (threshold to threshold*3 maps to 0-40)
            normalized = min(1.0, (z_score - threshold) / (threshold * 2))
            score = 40 * normalized + 30  # Base score of 30 for any spike
        else:
            score = 0.0
        
        return SignalResult(
            detected=is_spike,
            signal_type="volume_spike",
            score=score,
            details={
                "current_volume": current_volume,
                "mean_volume": mean_volume,
                "std_volume": std_volume,
                "z_score": z_score,
                "threshold": threshold,
                "data_points": len(volumes),
            }
        )
    
    async def detect_orderbook_imbalance(
        self,
        market_id: str,
        bid_depth: float,
        ask_depth: float,
    ) -> SignalResult:
        """
        Detect significant orderbook asymmetry.
        
        Imbalance occurs when one side of the book significantly
        outweighs the other, suggesting directional pressure.
        
        Args:
            market_id: Market to analyze
            bid_depth: Total bid liquidity (USD)
            ask_depth: Total ask liquidity (USD)
            
        Returns:
            SignalResult with detection status and details
        """
        # Calculate imbalance ratio
        if bid_depth == 0 and ask_depth == 0:
            return SignalResult(
                detected=False,
                signal_type="orderbook_imbalance",
                score=0.0,
                details={"reason": "no_liquidity"}
            )
        
        if bid_depth == 0 or ask_depth == 0:
            ratio = float('inf')
            direction = "bid" if ask_depth == 0 else "ask"
        else:
            ratio = max(bid_depth, ask_depth) / min(bid_depth, ask_depth)
            direction = "bid" if bid_depth > ask_depth else "ask"
        
        # Check thresholds
        threshold = self.settings.imbalance_threshold
        min_depth = self.settings.imbalance_minimum
        larger_side = max(bid_depth, ask_depth)
        
        is_imbalanced = (
            ratio >= threshold and
            larger_side >= min_depth
        )
        
        # Calculate score (0-100)
        if is_imbalanced:
            # Normalize ratio to 0-30 range
            normalized = min(1.0, (ratio - threshold) / (threshold * 2))
            score = 30 * normalized + 25  # Base score of 25
        else:
            score = 0.0
        
        return SignalResult(
            detected=is_imbalanced,
            signal_type="orderbook_imbalance",
            score=score,
            details={
                "bid_depth": bid_depth,
                "ask_depth": ask_depth,
                "ratio": ratio if ratio != float('inf') else "infinite",
                "direction": direction,
                "threshold": threshold,
            }
        )
    
    async def detect_price_divergence(
        self,
        market_id: str,
        current_price: float,
        current_volume: float,
    ) -> SignalResult:
        """
        Detect price-volume divergence.
        
        Divergence occurs when:
        - Price moves significantly without proportional volume
        - Volume spikes without proportional price movement
        
        Args:
            market_id: Market to analyze
            current_price: Current YES price
            current_volume: Current period volume
            
        Returns:
            SignalResult with detection status and details
        """
        # Get price from 1 hour ago
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        query = select(
            PriceSnapshotModel.yes_price,
            PriceSnapshotModel.volume
        ).where(
            PriceSnapshotModel.market_id == market_id,
            PriceSnapshotModel.timestamp <= one_hour_ago
        ).order_by(
            PriceSnapshotModel.timestamp.desc()
        ).limit(1)
        
        result = await self.session.execute(query)
        row = result.fetchone()
        
        if row is None:
            return SignalResult(
                detected=False,
                signal_type="price_divergence",
                score=0.0,
                details={"reason": "no_historical_data"}
            )
        
        historical_price, historical_volume = row
        
        # Calculate price change
        if historical_price == 0:
            price_change_pct = 0.0
        else:
            price_change_pct = abs(current_price - historical_price) / historical_price
        
        # Calculate expected volume for this price move
        # This is a simple model - could be made more sophisticated
        baseline_volume = historical_volume if historical_volume > 0 else 1000
        volume_sensitivity = 2.0  # Expected volume multiplier per 10% price change
        expected_volume = baseline_volume * (1 + price_change_pct * volume_sensitivity * 10)
        
        # Check for divergence
        price_threshold = self.settings.price_change_threshold
        
        # Type 1: Big price move, low volume (suspicious)
        price_without_volume = (
            price_change_pct > price_threshold and
            current_volume < expected_volume * 0.5
        )
        
        # Type 2: Big volume, no price move (accumulation?)
        volume_without_price = (
            current_volume > expected_volume * 2 and
            price_change_pct < price_threshold * 0.5
        )
        
        is_divergent = price_without_volume or volume_without_price
        
        # Calculate score
        if is_divergent:
            if price_without_volume:
                # Score based on how much price moved without volume
                normalized = min(1.0, price_change_pct / (price_threshold * 2))
                score = 35 * normalized + 25
                divergence_type = "price_without_volume"
            else:
                # Score based on volume excess
                volume_ratio = current_volume / expected_volume
                normalized = min(1.0, (volume_ratio - 2) / 3)
                score = 30 * normalized + 20
                divergence_type = "volume_without_price"
        else:
            score = 0.0
            divergence_type = None
        
        return SignalResult(
            detected=is_divergent,
            signal_type="price_divergence",
            score=score,
            details={
                "current_price": current_price,
                "historical_price": historical_price,
                "price_change_pct": price_change_pct,
                "current_volume": current_volume,
                "expected_volume": expected_volume,
                "divergence_type": divergence_type,
            }
        )
    
    async def save_signal(
        self,
        market_id: str,
        signal_result: SignalResult,
        price_at_signal: float,
        volume_at_signal: float,
    ) -> SignalModel:
        """
        Persist a detected signal to the database.
        
        Args:
            market_id: Market the signal was detected in
            signal_result: The detection result
            price_at_signal: Price when signal detected
            volume_at_signal: Volume when signal detected
            
        Returns:
            The created SignalModel
        """
        signal = SignalModel(
            market_id=market_id,
            signal_type=signal_result.signal_type,
            timestamp=datetime.utcnow(),
            score=signal_result.score,
            details=signal_result.details,
            price_at_signal=price_at_signal,
            volume_at_signal=volume_at_signal,
        )
        
        self.session.add(signal)
        await self.session.flush()
        
        return signal


# =============================================================================
# Utility functions
# =============================================================================

async def get_recent_signals(
    session: AsyncSession,
    limit: int = 20,
    min_score: float = 0.0,
    signal_type: Optional[str] = None,
) -> list[SignalModel]:
    """
    Fetch recent signals from the database.
    
    Args:
        session: Database session
        limit: Max signals to return
        min_score: Minimum score filter
        signal_type: Filter by type (optional)
        
    Returns:
        List of SignalModel objects
    """
    query = select(SignalModel).where(
        SignalModel.score >= min_score
    )
    
    if signal_type:
        query = query.where(SignalModel.signal_type == signal_type)
    
    query = query.order_by(
        SignalModel.timestamp.desc()
    ).limit(limit)
    
    result = await session.execute(query)
    return list(result.scalars().all())
