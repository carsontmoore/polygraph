# Learning Callouts

A running list of concepts, patterns, and gotchas encountered while building Polygraph. Use this as a reference guide.

---

## Python Fundamentals

### 1. Virtual Environments (venv)

A virtual environment is an isolated Python installation per project - like a sandbox.

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it (run once per terminal session)
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Your prompt shows (venv) when active
(venv) $ python --version

# Deactivate when done
deactivate
```

**Why use them?** Project isolation. Project A can use `pydantic==1.0` while Project B uses `pydantic==2.0` without conflicts.

**Key point:** Activation persists for your terminal session. You don't need to re-run `source venv/bin/activate` after editing files - only when opening a new terminal.

---

### 2. pyproject.toml

Python's modern equivalent to `package.json`. Consolidates project configuration in one file.

| Python (`pyproject.toml`) | JavaScript (`package.json`) |
|---------------------------|----------------------------|
| `[project]` section | `name`, `version` fields |
| `dependencies = [...]` | `"dependencies": {...}` |
| `[project.optional-dependencies]` | `"devDependencies": {...}` |

```toml
[project]
name = "polygraph"
version = "0.1.0"
dependencies = [
    "fastapi>=0.109.0",
    "sqlalchemy>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
]
```

**History:** Before `pyproject.toml`, Python had `setup.py`, `requirements.txt`, `setup.cfg`, and `MANIFEST.in`. The new format (PEP 518/621) consolidates everything.

---

### 3. Package Extras

Extras are optional dependency groups bundled with a package.

```bash
# Just the core package
pip install fastapi

# Core + "standard" extras (Swagger UI, uvicorn, etc.)
pip install "fastapi[standard]"

# Multiple extras
pip install "sqlalchemy[asyncio,postgresql]"
```

Common examples:
- `fastapi[standard]` - adds uvicorn, Swagger UI deps
- `uvicorn[standard]` - adds websocket support
- `sqlalchemy[asyncio]` - adds async support

---

### 4. pip install - When Directory Matters

| Command | Directory Matters? | Why |
|---------|-------------------|-----|
| `pip install fastapi` | No | Downloads from PyPI |
| `pip install "fastapi[standard]"` | No | Downloads from PyPI |
| `pip install -e .` | **Yes** | The `.` means "current directory's pyproject.toml" |
| `pip install -r requirements.txt` | **Yes** | Needs the file in current directory |

The `-e` flag means "editable" - changes to your code are immediately available without reinstalling.

---

### 5. Shell Escaping (zsh)

In zsh (default macOS shell), square brackets are special characters. Quote them:

```bash
# This fails in zsh:
pip install fastapi[standard]  # ❌ "no matches found"

# This works:
pip install "fastapi[standard]"  # ✅
```

---

## Pydantic & Data Validation

### 6. Pydantic Models

Pydantic validates data using Python type hints. When you define a model:

```python
class User(BaseModel):
    name: str
    age: int
```

Pydantic will:
1. Validate incoming data matches types
2. Convert where possible (`"42"` → `42` for int)
3. Raise clear errors on validation failure

---

### 7. @field_validator

Transform or clean data **before** Pydantic validates types.

```python
from pydantic import BaseModel, field_validator

class Market(BaseModel):
    outcomes: list[str] = []
    
    @field_validator('outcomes', mode='before')
    @classmethod
    def parse_json_string(cls, v):
        # API returns '["Yes", "No"]' as a string
        # We need ["Yes", "No"] as a list
        if isinstance(v, str):
            return json.loads(v)
        return v
```

**Key parameters:**
- First arg(s): field names to validate
- `mode='before'`: Run BEFORE type checking
- `mode='after'`: Run AFTER type checking (value already validated)

---

### 8. @classmethod

A method that belongs to the class, not an instance. Required for Pydantic validators.

```python
class Market(BaseModel):
    @field_validator('outcomes', mode='before')
    @classmethod  # Required - validator is called on the class
    def parse_outcomes(cls, v):  # 'cls' not 'self'
        return v
```

**Regular method:** `self.method()` - operates on instance data
**Class method:** `cls.method()` - operates on class itself

---

### 9. @property

Makes a method accessible like an attribute - Pythonic computed values.

```python
class Market(BaseModel):
    id: str | None = None
    condition_id: str | None = None
    
    @property
    def market_id(self) -> str:
        """Best available identifier."""
        return self.id or self.condition_id or "unknown"

# Usage:
market.market_id      # ✅ Looks like attribute access
market.market_id()    # ❌ Not this
```

---

### 10. ConfigDict (Pydantic v2)

Model-wide configuration options.

```python
from pydantic import BaseModel, ConfigDict

class Market(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,  # Accept "conditionId" AND "condition_id"
        extra="ignore",         # Don't fail on unexpected fields
    )
```

Common options:
- `populate_by_name`: Allow field aliases
- `extra="ignore"`: Silently drop unknown fields
- `extra="forbid"`: Error on unknown fields
- `str_strip_whitespace`: Auto-strip string whitespace

---

## APIs & Architecture

### 11. Public vs Private APIs

Many APIs have both public (read) and private (write) endpoints:

```
┌─────────────────────────────────────────┐
│           PUBLIC ENDPOINTS              │
│           (No auth needed)              │
├─────────────────────────────────────────┤
│  GET /markets    → List markets         │
│  GET /book       → Orderbook            │
│  GET /price      → Current price        │
│                                         │
│  Anyone can read. Intentional.          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          PRIVATE ENDPOINTS              │
│        (Auth/signature required)        │
├─────────────────────────────────────────┤
│  POST /order     → Place order          │
│  DELETE /order   → Cancel order         │
│  GET /positions  → Your holdings        │
└─────────────────────────────────────────┘
```

Polymarket uses wallet-based auth (cryptographic signatures), not API keys.

---

### 12. Handling Messy APIs

Real-world APIs often return inconsistent data:
- Fields might be camelCase or snake_case
- Lists might come as JSON strings: `'["a", "b"]'` instead of `["a", "b"]`
- Numbers might be strings or vice versa
- Fields might be missing entirely

**Solution:** Use Pydantic validators to normalize data before validation.

---

## JavaScript / Node.js

### 13. npm audit Context

Not all vulnerabilities are equal:

```
Dev dependency vulnerability → Usually ignorable
├── Only runs on YOUR machine during development
└── Never ships to users

Production dependency vulnerability → Take seriously
├── Runs in deployed application  
└── Could affect real users
```

The severity rating doesn't account for context. A "high" in a dev tool you never invoke is less urgent than a "low" in user-facing code.

**Don't blindly run `npm audit fix --force`** - it can introduce breaking changes. Check what's affected first with `npm audit`.

---

## Debugging Lessons

### 14. Check the Actual Request Path

When getting 404s, check the server logs for the actual path being requested:

```
GET /api/docs HTTP/1.1" 404    ← Wrong path
GET /docs HTTP/1.1" 200        ← Correct path
```

FastAPI's `/docs` is at the root, not under `/api` (unless explicitly configured).

---

## Commands Quick Reference

```bash
# Python Virtual Environment
python3 -m venv venv          # Create
source venv/bin/activate      # Activate (macOS/Linux)
deactivate                    # Deactivate
pip install -e .              # Install project in editable mode
pip install "package[extra]"  # Install with extras (quote for zsh)

# Running the Backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Running the Frontend
npm install                   # Install dependencies
npm run dev                   # Start dev server

# Git Checkpoint
git add .
git commit -m "description"
git push origin main

# Debugging
python -c "print('test')"     # Run one-liner
lsof -i :8000                 # Check what's using port 8000
kill -9 <PID>                 # Force kill process
```

---

*This document is updated as new concepts are encountered during development.* s