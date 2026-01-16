"""
Polygraph API Server

Main FastAPI application that serves the prediction market analytics API.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.database import initialize_database, close_database
from src.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    print("🚀 Starting Polygraph API server...")
    await initialize_database()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Polygraph API server...")
    await close_database()
    print("✅ Database connections closed")


# Create the FastAPI application
app = FastAPI(
    title="Polygraph API",
    description="Prediction market analytics and signal detection for Polymarket",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend access
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "https://*.vercel.app",   # Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Polygraph API",
        "version": "0.1.0",
        "description": "Prediction market analytics for Polymarket",
        "docs": "/docs",
        "health": "/api/health",
    }


# =============================================================================
# Development server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
