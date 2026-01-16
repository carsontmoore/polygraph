# Polygraph

**Prediction market analytics and signal detection for Polymarket.**

Polygraph monitors Polymarket prediction markets in real-time, detecting unusual trading patterns like volume spikes, orderbook imbalances, and price divergences that may indicate informed trading activity.

## Project Structure

```
polygraph/
├── backend/               # Python FastAPI backend
│   ├── src/
│   │   ├── api/          # REST API endpoints
│   │   ├── ingestion/    # Polymarket API client
│   │   ├── signals/      # Signal detection algorithms
│   │   ├── config.py     # Configuration management
│   │   ├── database.py   # SQLAlchemy models & DB setup
│   │   ├── main.py       # FastAPI application
│   │   └── models.py     # Pydantic models
│   ├── pyproject.toml
│   └── test_api.py       # API validation script
│
├── frontend/             # Next.js React frontend
│   ├── src/
│   │   ├── app/          # Next.js app router pages
│   │   ├── components/   # Reusable React components
│   │   └── lib/          # API client & utilities
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run the API server
python -m src.main
# Or with uvicorn directly:
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/markets` | GET | List tracked markets |
| `/api/markets/{id}` | GET | Get market detail with history |
| `/api/signals` | GET | List detected signals |
| `/api/signals/top` | GET | Get highest-scoring signals |
| `/api/stats` | GET | Dashboard statistics |
| `/api/health` | GET | Health check |

## Signal Types

### Volume Spike
Detected when trading volume exceeds 2.5 standard deviations from the 24-hour rolling average.

### Orderbook Imbalance
Detected when bid or ask depth exceeds 3x the opposite side, indicating directional pressure.

### Price Divergence
Detected when price moves significantly without proportional volume (or vice versa).

## Configuration

Environment variables (create `.env` in backend directory):

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./polygraph.db

# Polling intervals (seconds)
PRICE_POLL_INTERVAL=60
MARKET_REFRESH_INTERVAL=300

# Signal thresholds
VOLUME_SPIKE_THRESHOLD=2.5
VOLUME_MINIMUM=10000
IMBALANCE_THRESHOLD=3.0
IMBALANCE_MINIMUM=5000
PRICE_CHANGE_THRESHOLD=0.05

# Limits
MAX_TRACKED_MARKETS=50

# Debug
DEBUG=true
```

## Development Roadmap

### Phase 1: Foundation ✅
- [x] Project structure
- [x] Polymarket API client
- [x] Database schema
- [x] Signal detection algorithms
- [x] FastAPI endpoints
- [x] Next.js frontend scaffold

### Phase 2: Real-Time (Next)
- [ ] WebSocket data ingestion
- [ ] Redis for real-time state
- [ ] Live signal feed
- [ ] Background polling service

### Phase 3: Advanced Signals
- [ ] Cross-market correlation
- [ ] Wallet tracking
- [ ] Backtesting framework
- [ ] Alert notifications

### Phase 4: Distribution
- [ ] Twitter/X bot
- [ ] Telegram integration
- [ ] Chart generation
- [ ] Content templates

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- Pydantic
- httpx

**Frontend:**
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Recharts

**Infrastructure:**
- SQLite (development) → PostgreSQL/TimescaleDB (production)
- Vercel (frontend hosting)
- Railway/Render (backend hosting)

## License

MIT
