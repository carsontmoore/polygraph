# Polymarket API Access: Challenge & Solutions

## The Problem

When running from cloud/datacenter environments (AWS, GCP, Vercel, Railway, etc.), Polymarket's APIs return `403 Forbidden` errors due to Cloudflare protection that blocks datacenter IPs.

This affects:
- Gamma API (`gamma-api.polymarket.com`) 
- CLOB API (`clob.polymarket.com`)
- Goldsky subgraphs
- Main polymarket.com endpoints

## Why This Happens

Polymarket uses aggressive Cloudflare protection to:
1. Prevent automated trading bots from overwhelming the system
2. Enforce geographic restrictions (US, UK, France, etc. are blocked)
3. Rate limit API access

Cloudflare can distinguish between:
- Residential IPs (allowed)
- Datacenter IPs (blocked or challenged)
- Known VPN exit nodes (sometimes blocked)

## Solutions

### Option 1: Develop Locally, Deploy Differently

**For Development:**
- Run the Python data ingestion script locally on your machine
- Your residential IP won't be blocked
- Test and validate the API integration locally

**For Production:**
- Use a proxy service with residential IPs
- Consider a VPS with a residential IP provider
- Use Cloudflare Workers (they have better trust scores with Cloudflare)

### Option 2: Use Alternative Data Sources

**On-Chain Data (No Cloudflare):**
- Query Polygon blockchain directly via RPC
- Use services like Alchemy or Infura for blockchain data
- Parse smart contract events for trade data

**Third-Party Aggregators:**
- Bitquery (blockchain data API)
- Dune Analytics (can query Polymarket data)
- The Graph (decentralized subgraphs)

### Option 3: Residential Proxy Service

Services that provide residential IPs for API access:
- Bright Data (Luminati)
- Oxylabs
- Smartproxy

**Cost:** ~$10-50/month for basic usage

### Option 4: Run on Residential Hardware

- Raspberry Pi at home running the data ingestion
- Old laptop as a home server
- Cheap mini PC

**Setup:**
```bash
# On your home machine
python data_ingestion.py --mode=collector

# Sync data to cloud database
# Or expose via API for your Vercel frontend
```

## Recommended Architecture

Given the constraints, here's the recommended approach:

```
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│  Home Server       │     │  Cloud Database    │     │  Vercel Frontend   │
│  (Residential IP)  │────▶│  (Supabase/        │◀────│  (Next.js)         │
│                    │     │   PlanetScale)     │     │                    │
│  - Data ingestion  │     │                    │     │  - Dashboard UI    │
│  - Signal detection│     │  - Market data     │     │  - API routes      │
│  - Polymarket API  │     │  - Price history   │     │  - No direct PM    │
│    access          │     │  - Signals         │     │    API calls       │
└────────────────────┘     └────────────────────┘     └────────────────────┘
```

**Why this works:**
1. Home server has residential IP → Polymarket APIs accessible
2. Cloud database is publicly accessible → Both can connect
3. Vercel frontend reads from database → No Polymarket API needed
4. Signal detection runs on home server → Writes alerts to database
5. Frontend displays data → Users see real-time-ish updates

## For Now: Mock Data Development

While you set up residential access, we can:

1. **Build with mock data** - Create realistic sample data structures
2. **Design the full system** - Database schema, API routes, UI components
3. **Test locally when possible** - Run scripts from your local machine

This lets us make progress on the frontend and signal detection logic while you solve the infrastructure piece.

## Testing Locally

To verify the APIs work from your machine:

```python
# save as test_local.py
import httpx

url = "https://gamma-api.polymarket.com/markets?limit=1&active=true"
resp = httpx.get(url)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print("✓ API accessible from your IP!")
    print(resp.json())
else:
    print("✗ Still blocked - may need VPN or different network")
```

Run this from your local machine (not cloud) to verify access.

## Next Steps

1. Test API access from your local machine
2. If working, set up a local data collection script
3. Choose a cloud database (Supabase recommended - free tier, good DX)
4. Build the frontend against the database
5. Deploy data collector to home hardware or residential VPS

---

*This is a common challenge when building fintech/crypto tools. The solution is architectural - separate data collection (needs residential IP) from data presentation (can be anywhere).*
