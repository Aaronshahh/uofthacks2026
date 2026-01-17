"""
FastAPI application for the Footwear RAG Agent.
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from .config import get_config
from .models import HealthResponse
from .database import SnowflakeVectorDB
from .routes import ingest, query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Footwear RAG Agent...")
    try:
        config = get_config()
        logger.info(f"Configuration loaded successfully")
        logger.info(f"API will run on {config.api.host}:{config.api.port}")
    except Exception as e:
        logger.warning(f"Failed to load config: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Footwear RAG Agent...")


# Create FastAPI app
app = FastAPI(
    title="Footwear RAG Agent API",
    description="""
    A forensic footwear analysis system that uses RAG (Retrieval-Augmented Generation) 
    to find similar footprints and provide metadata insights.
    
    ## Features
    
    - **Data Ingestion**: Process zip files containing footprint images and CSV metadata
    - **RAG Query**: Upload a footprint image to find the 3 most similar matches
    - **Metadata Cases**: Returns 3 possible cases (A, B, C) with full metadata
    
    ## Query Flow
    
    1. Upload a footprint image
    2. System embeds the image and searches the vector database
    3. Returns top 3 closest matches as separate metadata cases
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
try:
    config = get_config()
    origins = config.api.cors_origins
except:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router)
app.include_router(query.router)

# Serve frontend static files
FRONTEND_PATH = Path(__file__).parent.parent / "frontend"
logger.info(f"Frontend path: {FRONTEND_PATH} (exists: {FRONTEND_PATH.exists()})")

if FRONTEND_PATH.exists():
    # Mount static files directory
    app.mount("/static", StaticFiles(directory=str(FRONTEND_PATH)), name="static")
    logger.info(f"Static files mounted from: {FRONTEND_PATH}")


@app.get("/styles.css", include_in_schema=False)
async def styles():
    """Serve CSS file."""
    css_path = FRONTEND_PATH / "styles.css"
    if css_path.exists():
        return FileResponse(str(css_path), media_type="text/css")
    raise HTTPException(status_code=404, detail="styles.css not found")


@app.get("/app.js", include_in_schema=False)
async def app_js():
    """Serve JavaScript file."""
    js_path = FRONTEND_PATH / "app.js"
    if js_path.exists():
        return FileResponse(str(js_path), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app.js not found")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the frontend application."""
    index_path = FRONTEND_PATH / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return {"message": "Footwear RAG Agent API", "docs": "/docs"}


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="Check the health status of the API and database connection"
)
async def health_check():
    """
    Check the health of the API and database connection.
    
    Returns:
        HealthResponse with status and database info
    """
    try:
        db = SnowflakeVectorDB()
        record_count = db.get_record_count()
        db_connected = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_connected = False
        record_count = 0
    
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        database_connected=db_connected,
        record_count=record_count,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/info", tags=["info"])
async def api_info():
    """Get API information and configuration (non-sensitive)."""
    return {
        "name": "Footwear RAG Agent",
        "version": "1.0.0",
        "description": "Forensic footwear analysis using RAG",
        "endpoints": {
            "query": "/api/query",
            "ingest": "/api/ingest",
            "health": "/api/health"
        }
    }


def run_server():
    """Run the FastAPI server using uvicorn."""
    import uvicorn
    
    try:
        config = get_config()
        host = config.api.host
        port = config.api.port
    except:
        host = "0.0.0.0"
        port = 8000
    
    uvicorn.run(
        "footwear_rag.backend.main:app",
        host=host,
        port=port,
        reload=True
    )


if __name__ == "__main__":
    run_server()
