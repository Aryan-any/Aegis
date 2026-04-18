from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import router
from app.db.database import create_db_and_tables
import uuid
import time
import logging

# --- Professional Telemetry Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SagePilot-API")

app = FastAPI(
    title="Aegis Order Supervisor API",
    version="2.0.0",
    description="Professional-grade autonomous order supervision backend."
)

@app.middleware("http")
async def add_trace_id_middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    start_time = time.time()
    
    logger.info(f"[TRACE:{trace_id}] {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Trace-ID"] = trace_id
    logger.info(f"[TRACE:{trace_id}] Completed in {process_time:.4f}s")
    
    return response

# --- Middleware & Routing ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Include decoupled routes
app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}
