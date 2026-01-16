# Polymarket Analytics Platform - Project Specification

> **Working Title:** PolyGraph / PolyPulse / PolyGlot (TBD)
> **Version:** 0.1 - Initial Planning
> **Last Updated:** January 2026

---

## Executive Summary

A real-time analytics platform for Polymarket prediction markets that detects "smart money" signals, unusual volume divergences, and whale activity—then surfaces these insights via a web dashboard and automated social media alerts.

**Primary Goals:**
1. Learn Python data engineering and Next.js frontend development
2. Build a functional product that provides genuine value to prediction market participants
3. Create a foundation for audience building and professional networking

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│   │  Polymarket     │     │  Polymarket     │     │  Polymarket     │       │
│   │  CLOB REST API  │     │  WebSocket      │     │  Gamma API      │       │
│   │  (Historical)   │     │  (Real-time)    │     │  (Metadata)     │       │
│   └────────┬────────┘     └────────┬────────┘     └────────┬────────┘       │
│            │                       │                       │                 │
│            └───────────────────────┼───────────────────────┘                 │
│                                    │                                         │
│                                    ▼                                         │
│                        ┌─────────────────────┐                               │
│                        │   Data Ingestion    │                               │
│                        │   Service (Python)  │                               │
│                        └──────────┬──────────┘                               │
│                                   │                                          │
└───────────────────────────────────┼──────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            STORAGE LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│   │   PostgreSQL    │     │     Redis       │     │   File Storage  │       │
│   │   (TimescaleDB) │     │   (Real-time    │     │   (Charts/      │       │
│   │                 │     │    State)       │     │    Images)      │       │
│   └─────────────────┘     └─────────────────┘     └─────────────────┘       │
│                                                                              │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                    Signal Detection Engine                       │       │
│   │                                                                  │       │
│   │   • Volume Anomaly Detection                                     │       │
│   │   • Price/Volume Divergence Analysis                             │       │
│   │   • New Wallet Activity Flagging                                 │       │
│   │   • Cross-Market Correlation Detection                           │       │
│   │   • Configurable Alert Thresholds                                │       │
│   │                                                                  │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌───────────────────────────────────┐   ┌───────────────────────────────────┐
│       PRESENTATION LAYER          │   │      DISTRIBUTION LAYER           │
├───────────────────────────────────┤   ├───────────────────────────────────┤
│                                   │   │                                   │
│   Next.js Web Application         │   │   Social Bot Service              │
│                                   │   │                                   │
│   • Dashboard UI                  │   │   • Twitter/X API                 │
│   • Market Explorer               │   │   • Telegram Bot (future)         │
│   • Signal Feed                   │   │   • Auto-generated Charts         │
│   • Alert Configuration           │   │   • Rate Limiting                 │
│   • Historical Analysis           │   │                                   │
│                                   │   │                                   │
└───────────────────────────────────┘   └───────────────────────────────────┘
```

---

## Phase 1: Foundation (Current Sprint)

### Objectives
- Establish connection to Polymarket APIs
- Build minimal data ingestion pipeline
- Store market data in a queryable format
- Deploy basic Next.js dashboard with real data
- Implement one simple signal detection algorithm

### Deliverables

#### 1.1 Data Ingestion Service (Python)

**Scope:**
- Connect to Polymarket CLOB REST API
- Fetch market metadata from Gamma API
- Pull historical price/volume data for selected markets
- Store in SQLite initially (upgrade to TimescaleDB in Phase 2)

**Initial Market Selection:**
- Start with 5-10 high-volume, active markets
- Focus on diverse categories (politics, crypto, sports)
- Prioritize markets with sufficient historical data

**API Endpoints to Integrate:**

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `GET /markets` (Gamma) | Market metadata, categories | P0 |
| `GET /book` (CLOB) | Current orderbook snapshot | P0 |
| `GET /price` (CLOB) | Current price for token | P0 |
| `GET /prices-history` (CLOB) | Historical price timeseries | P0 |
| `WSS /ws/market` (CLOB) | Real-time orderbook updates | P1 |

**Data Models:**

```python
# Market metadata
class Market:
    condition_id: str           # Unique market identifier
    question: str               # "Will X happen?"
    category: str               # politics, crypto, sports, etc.
    end_date: datetime          # Resolution date
    tokens: List[Token]         # YES/NO token details
    active: bool
    closed: bool

# Token (outcome)
class Token:
    token_id: str
    outcome: str                # "Yes" or "No"
    price: float                # Current price (0-1)

# Price snapshot
class PriceSnapshot:
    market_id: str
    token_id: str
    timestamp: datetime
    price: float
    bid: float
    ask: float
    spread: float

# Trade (for future use)
class Trade:
    market_id: str
    token_id: str
    timestamp: datetime
    price: float
    size: float
    side: str                   # BUY or SELL
```

#### 1.2 Next.js Web Application

**Scope:**
- Basic dashboard layout
- Market list view with current prices
- Individual market detail page
- Simple price chart (historical)
- Signal/alert feed (placeholder initially)

**Tech Stack:**
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- Recharts or Plotly for visualization
- Deployed on Vercel

**Pages:**

| Route | Description |
|-------|-------------|
| `/` | Dashboard home - market overview, recent signals |
| `/markets` | Searchable/filterable market list |
| `/markets/[id]` | Individual market detail with charts |
| `/signals` | Signal feed with filtering |
| `/about` | Platform description |

#### 1.3 Signal Detection v0.1

**Initial Algorithm: Volume Spike Detection**

Start simple - detect when trading volume significantly exceeds recent baseline.

```python
def detect_volume_spike(
    market_id: str,
    current_volume: float,
    lookback_hours: int = 24,
    threshold_multiplier: float = 3.0
) -> Optional[Signal]:
    """
    Detect if current volume exceeds N standard deviations
    above the rolling average.
    """
    baseline = get_rolling_average_volume(market_id, lookback_hours)
    std_dev = get_rolling_std_dev(market_id, lookback_hours)
    
    if current_volume > baseline + (threshold_multiplier * std_dev):
        return Signal(
            type="VOLUME_SPIKE",
            market_id=market_id,
            severity=calculate_severity(current_volume, baseline, std_dev),
            timestamp=datetime.utcnow(),
            metadata={
                "current_volume": current_volume,
                "baseline": baseline,
                "multiplier": (current_volume - baseline) / std_dev
            }
        )
    return None
```

**Signal Output Format:**

```json
{
  "id": "sig_abc123",
  "type": "VOLUME_SPIKE",
  "market": {
    "id": "0x1234...",
    "question": "Will Bitcoin reach $150k by June 2026?"
  },
  "severity": "HIGH",
  "timestamp": "2026-01-16T14:30:00Z",
  "summary": "Trading volume 4.2x above 24h average",
  "metadata": {
    "current_volume": 125000,
    "baseline_volume": 29762,
    "std_dev_multiplier": 4.2
  }
}
```

---

## Phase 2: Enhanced Detection (Future)

### Additional Signal Types

1. **Price/Volume Divergence**
   - Price moving without corresponding volume (weak conviction)
   - Volume surging without price movement (accumulation/distribution)

2. **New Wallet Activity**
   - Large orders from wallets with no prior Polymarket history
   - Requires on-chain data integration

3. **Cross-Market Correlation**
   - Detecting when related markets move in sequence
   - E.g., "Will Trump win?" moving before "Will Republicans win Senate?"

4. **Orderbook Imbalance**
   - Bid/ask ratio shifts indicating directional pressure
   - Large orders appearing/disappearing

5. **Smart Money Following**
   - Tracking wallets with historically high win rates
   - Alerting when known profitable traders take positions

---

## Phase 3: Distribution (Future)

### Social Media Integration

- Automated posting to Twitter/X when high-confidence signals detected
- Chart generation for visual appeal
- Rate limiting to avoid spam
- Human-in-the-loop approval for v1

### Telegram Bot

- Real-time alerts for subscribers
- Configurable filters (market type, severity threshold)
- Potential monetization path

---

## Technical Decisions

### Why Python for Data Pipeline?

- Rich ecosystem for data processing (pandas, numpy)
- Excellent async support for WebSocket handling
- Carson's learning objective
- Easy integration with ML libraries for future signal enhancement

### Why Next.js for Frontend?

- Modern React patterns (Server Components, App Router)
- Built-in API routes for BFF pattern
- Vercel deployment simplicity
- Carson's learning objective

### Why SQLite Initially?

- Zero infrastructure overhead
- Sufficient for Phase 1 data volumes
- Easy migration path to PostgreSQL/TimescaleDB
- Enables rapid iteration

### Future Infrastructure Considerations

- **TimescaleDB**: When time-series queries become bottleneck
- **Redis**: When real-time state management needed
- **Celery/RQ**: When background job processing required
- **Docker**: When deployment complexity warrants containerization

---

## Development Environment Setup

### Prerequisites

```bash
# Python 3.11+
python --version

# Node.js 18+
node --version

# Package managers
pip --version
npm --version
```

### Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

**Core Dependencies:**
```
httpx              # Async HTTP client
websockets         # WebSocket client
pandas             # Data manipulation
numpy              # Numerical operations
sqlalchemy         # Database ORM
sqlite-utils       # SQLite utilities
python-dotenv      # Environment management
pydantic           # Data validation
pytest             # Testing
```

### Next.js Environment

```bash
# Create Next.js app
npx create-next-app@latest polygraph-web --typescript --tailwind --app

# Install additional dependencies
npm install recharts @tanstack/react-query axios date-fns
```

---

## API Reference

### Polymarket CLOB API

**Base URL:** `https://clob.polymarket.com`

**Get Markets:**
```bash
curl https://clob.polymarket.com/markets
```

**Get Orderbook:**
```bash
curl "https://clob.polymarket.com/book?token_id={TOKEN_ID}"
```

**Get Price:**
```bash
curl "https://clob.polymarket.com/price?token_id={TOKEN_ID}&side=BUY"
```

### Polymarket Gamma API

**Base URL:** `https://gamma-api.polymarket.com`

**Get Events:**
```bash
curl https://gamma-api.polymarket.com/events
```

**Get Markets:**
```bash
curl https://gamma-api.polymarket.com/markets
```

### WebSocket (Real-time)

**URL:** `wss://ws-subscriptions-clob.polymarket.com/ws/market`

**Subscribe to Market:**
```json
{
  "type": "subscribe",
  "channel": "market",
  "markets": ["MARKET_CONDITION_ID"]
}
```

---

## File Structure

```
polygraph/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point
│   │   ├── config.py            # Configuration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── clob.py          # CLOB API client
│   │   │   ├── gamma.py         # Gamma API client
│   │   │   └── websocket.py     # WebSocket handler
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── market.py
│   │   │   ├── price.py
│   │   │   └── signal.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   └── migrations/
│   │   ├── signals/
│   │   │   ├── __init__.py
│   │   │   ├── detector.py      # Signal detection engine
│   │   │   └── volume.py        # Volume spike detection
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── tests/
│   │   └── ...
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx         # Dashboard
│   │   │   ├── markets/
│   │   │   │   ├── page.tsx     # Market list
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx # Market detail
│   │   │   └── signals/
│   │   │       └── page.tsx     # Signal feed
│   │   ├── components/
│   │   │   ├── MarketCard.tsx
│   │   │   ├── PriceChart.tsx
│   │   │   ├── SignalFeed.tsx
│   │   │   └── ...
│   │   ├── lib/
│   │   │   ├── api.ts           # API client
│   │   │   └── types.ts         # TypeScript types
│   │   └── styles/
│   ├── package.json
│   └── .env.example
│
├── docs/
│   └── PROJECT_SPEC.md          # This document
│
└── README.md
```

---

## Success Criteria (Phase 1)

| Criteria | Measurement |
|----------|-------------|
| Data pipeline functional | Successfully fetching and storing data from 5+ markets |
| Dashboard deployed | Accessible via Vercel URL |
| Real data displayed | Markets showing live prices from Polymarket |
| Signal detection working | Volume spike alerts generating for test markets |
| Code quality | Typed Python, TypeScript throughout |
| Documentation | README with setup instructions |

---

## Open Questions

1. **Database hosting**: Vercel Postgres? PlanetScale? Railway? Self-hosted?
2. **API hosting for Python backend**: Railway? Render? AWS Lambda?
3. **Rate limiting strategy**: How aggressive can we poll without getting blocked?
4. **Historical data depth**: How far back do we need for meaningful baselines?
5. **Signal persistence**: Store all signals or just active/recent ones?

---

## Next Steps

1. [ ] Validate Polymarket API access with simple Python script
2. [ ] Define initial market selection criteria
3. [ ] Scaffold Python project structure
4. [ ] Scaffold Next.js project structure
5. [ ] Implement basic data fetching
6. [ ] Design database schema
7. [ ] Build first API endpoint
8. [ ] Create dashboard wireframes
9. [ ] Deploy MVP to Vercel

---

*Document maintained by Carson & Claude. Last sprint: January 2026.*
