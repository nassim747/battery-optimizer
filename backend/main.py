"""
Battery Optimization Microservice
FastAPI application with API-key auth, rate limiting, and request logging.
"""

import os
import time
import logging
import uuid
from collections import defaultdict
from typing import Dict, List

from fastapi import FastAPI, Depends, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse

from models import OptimizeRequest, OptimizeResponse, VisualizeResponse
from optimizer import run_optimization, build_visualize_data

API_KEYS: set = set(
    filter(None, os.getenv("API_KEYS", "dev-key-abc123,test-key-xyz789").split(","))
)
RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
ALLOWED_ORIGINS: List[str] = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("battery_api")

app = FastAPI(
    title="Battery Optimization API",
    description=(
        "Microservice that schedules battery charge/discharge over 24 hours "
        "to minimise electricity costs while respecting physical constraints."
    ),
    version="1.0.0",
    contact={"name": "Dunsky Energy", "email": "api@dunsky.example.com"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

_request_log: Dict[str, List[float]] = defaultdict(list)


def get_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key or api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return api_key


def rate_limit(api_key: str = Depends(get_api_key)) -> str:
    now = time.time()
    window = 60.0
    timestamps = _request_log[api_key]
    _request_log[api_key] = [t for t in timestamps if now - t < window]
    if len(_request_log[api_key]) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: max {RATE_LIMIT_PER_MINUTE} requests/min per key.",
        )
    _request_log[api_key].append(now)
    return api_key


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    logger.info(
        "→ %s %s %s [req=%s]",
        request.method,
        request.url.path,
        request.client.host if request.client else "unknown",
        request_id,
    )
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "← %s %s %dms [req=%s]",
        response.status_code,
        request.url.path,
        elapsed,
        request_id,
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", tags=["Meta"], summary="Service health check")
def health():
    """Returns service status and version."""
    return {"status": "ok", "version": "1.0.0", "service": "battery-optimization-api"}


@app.post(
    "/optimize",
    response_model=OptimizeResponse,
    tags=["Optimization"],
    summary="Compute 24-hour battery dispatch schedule",
)
def optimize(
    body: OptimizeRequest,
    _key: str = Depends(rate_limit),
):
    """
    Solves a Mixed-Integer Linear Program to minimise electricity cost over
    24 one-hour intervals, subject to battery physical constraints.

    Returns the optimal charge/discharge schedule, SoC trajectory, cost
    comparison, and a plain-language explanation of the top-saving hours.
    """
    logger.info(
        "optimize | battery capacity=%.1f kWh, efficiency=%.2f",
        body.battery.capacity_kwh,
        body.battery.efficiency,
    )
    try:
        result = run_optimization(
            load_kwh=body.load_kwh,
            price_per_kwh=body.price_per_kwh,
            capacity_kwh=body.battery.capacity_kwh,
            max_charge_kw=body.battery.max_charge_kw,
            max_discharge_kw=body.battery.max_discharge_kw,
            efficiency=body.battery.efficiency,
            initial_soc_kwh=body.battery.initial_soc_kwh,
        )
    except ValueError as exc:
        logger.error("optimize failed: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))

    logger.info(
        "optimize | savings=$%.2f (before=$%.2f, after=$%.2f)",
        result["savings"],
        result["total_cost_before"],
        result["total_cost_after"],
    )
    return result


@app.post(
    "/visualize",
    response_model=VisualizeResponse,
    tags=["Visualization"],
    summary="Return Plotly-ready chart data for the optimised schedule",
)
def visualize(
    body: OptimizeRequest,
    _key: str = Depends(rate_limit),
):
    """
    Runs the same optimisation as `/optimize` then formats the results as
    Plotly-compatible trace objects plus a summary section.
    """
    logger.info("visualize | battery capacity=%.1f kWh", body.battery.capacity_kwh)
    try:
        result = run_optimization(
            load_kwh=body.load_kwh,
            price_per_kwh=body.price_per_kwh,
            capacity_kwh=body.battery.capacity_kwh,
            max_charge_kw=body.battery.max_charge_kw,
            max_discharge_kw=body.battery.max_discharge_kw,
            efficiency=body.battery.efficiency,
            initial_soc_kwh=body.battery.initial_soc_kwh,
        )
    except ValueError as exc:
        logger.error("visualize failed: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))

    viz = build_visualize_data(
        load_kwh=body.load_kwh,
        price_per_kwh=body.price_per_kwh,
        charge_kw=result["charge_kw"],
        discharge_kw=result["discharge_kw"],
        soc_kwh=result["soc_kwh"],
        total_cost_before=result["total_cost_before"],
        total_cost_after=result["total_cost_after"],
        savings=result["savings"],
    )
    viz["explanation"] = result["explanation"]
    return viz
