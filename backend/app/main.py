import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_v1_router
from app.retrieval.chroma_store import retriever

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("fleetops")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing FleetOps AI Backend...")
    # 1. Initialize DB tables
    await init_db()
    logger.info("Database initialized successfully.")
    
    # 2. Ingest SOPs if collection is empty
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sop_dir = os.path.join(base_dir, "data", "sops")
    try:
        col = retriever.get_or_create_collection()
        if col.count() == 0 and os.path.exists(sop_dir):
            logger.info("ChromaDB SOP collection empty. Running initial ingestion...")
            count = retriever.ingest_sop_directory(sop_dir)
            logger.info(f"Ingested {count} procedure chunks.")
    except Exception as e:
        logger.warning(f"Could not initialize ChromaDB SOPs at startup: {e}")

    yield

    logger.info("Shutting down FleetOps AI Backend.")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Agentic Drone Incident Investigation & Safe Response System",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
cors_origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "operational",
        "docs_url": "/docs",
        "api_v1_prefix": settings.API_V1_PREFIX
    }
