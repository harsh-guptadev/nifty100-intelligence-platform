import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os

from src.api.routers import (
    health,
    companies,
    screener,
    sectors,
    peers,
    valuation,
    portfolio,
    documents
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_logger")

app = FastAPI(
    title="Nifty 100 Financial Intelligence REST API",
    description="REST API layer serving company fundamentals, KPIs, peer groups, screeners, and financial documents.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(f"Method: {request.method} Path: {request.url.path} Status: {response.status_code} Latency: {process_time:.2f}ms")
    return response

# Register all routers under /api/v1 prefix
app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(screener.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(peers.router, prefix="/api/v1")
app.include_router(valuation.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "message": "Nifty 100 Financial Intelligence REST API is running",
        "docs_url": "/docs",
        "health_url": "/api/v1/health"
    }

def export_openapi_spec():
    os.makedirs("docs", exist_ok=True)
    openapi_schema = app.openapi()
    with open("docs/openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("Exported docs/openapi.json")

if __name__ == "__main__":
    export_openapi_spec()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
