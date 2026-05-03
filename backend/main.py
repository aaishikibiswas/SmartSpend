import asyncio
import json
import logging
import os
import threading
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.requests import Request
from backend.models.train import train_regression_model
from backend.logging_config import setup_logging
from backend.services.pipeline import get_current_snapshot
from backend.services.websocket_manager import websocket_manager
from backend.storage import Storage

setup_logging()
logger = logging.getLogger("smartspend.api")

app = FastAPI(title="SmartSpend AI Platform API", version="1.0")

default_allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

env_allowed_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]

allowed_origins = sorted(set(default_allowed_origins + env_allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=os.getenv(
        "FRONTEND_ORIGIN_REGEX",
        r"https?://(localhost|127\.0\.0\.1):\d+|https://.*\.vercel\.app",
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from backend.routes import alerts, assistant, auth, bills, budget, cashflow, dashboard, decision, emi, expense_split, goals, networth, prediction, priorities, research, simulate, subscriptions, transactions, upload

    app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
    app.include_router(prediction.router, prefix="/predict", tags=["Prediction"])
    app.include_router(upload.router, prefix="/upload", tags=["Upload"])
    app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(assistant.router, prefix="/assistant", tags=["Assistant"])
    app.include_router(budget.router, prefix="/budget", tags=["Budget"])
    app.include_router(decision.router, prefix="/decision", tags=["Decision"])
    app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
    app.include_router(goals.router, prefix="/goals", tags=["Goals"])
    app.include_router(bills.router, prefix="/bills", tags=["Bills"])
    app.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
    app.include_router(emi.router, prefix="/emi", tags=["EMI"])
    app.include_router(expense_split.router, prefix="/expense-split", tags=["Expense Split"])
    app.include_router(networth.router, prefix="/networth", tags=["Net Worth"])
    app.include_router(cashflow.router, prefix="/cashflow", tags=["Cash Flow"])
    app.include_router(priorities.router, prefix="/priorities", tags=["Priorities"])
    app.include_router(simulate.router, prefix="/simulate", tags=["Simulator"])
    app.include_router(research.router, prefix="/research", tags=["Research"])
except ImportError as exc:
    print(f"Warning: Routes not fully initialized yet. {exc}")


@app.get("/")
def read_root():
    return {"message": "Welcome to the SmartSpend AI Backend API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Request failed | method=%s path=%s", request.method, request.url.path)
        raise

    # Request-level INFO logs are intentionally muted for cleaner terminals.
    # Uncomment this block when you want per-request timing again.
    # duration_ms = (time.perf_counter() - started) * 1000
    # logger.info(
    #     "Request completed | method=%s path=%s status=%s duration_ms=%.2f",
    #     request.method,
    #     request.url.path,
    #     response.status_code,
    #     duration_ms,
    # )
    return response


@app.on_event("startup")
def warm_up_models():
    def _run_training() -> None:
        try:
            transactions = Storage.get_transactions()
            if not transactions.empty:
                train_regression_model(transactions)
        except Exception:
            logger.exception("Background model warm-up failed")

    threading.Thread(target=_run_training, daemon=True).start()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    user = Storage.get_user_by_session(token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket_manager.connect(websocket)
    try:
        snapshot = await get_current_snapshot()
        snapshot["user"] = user
        await websocket_manager.send_json(websocket, snapshot)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception:
        websocket_manager.disconnect(websocket)


@app.get("/sse")
async def sse_endpoint(request: Request, token: str = ""):
    user = Storage.get_user_by_session(token)
    if user is None:
        return StreamingResponse(
            iter([f"event: error\ndata: {json.dumps({'message': 'Authentication required.'})}\n\n"]),
            status_code=401,
            media_type="text/event-stream",
        )

    async def event_generator():
        connection_id, queue = websocket_manager.connect_sse()
        try:
            snapshot = await get_current_snapshot()
            snapshot["user"] = user
            yield f"event: {snapshot.get('type', 'snapshot')}\ndata: {json.dumps(snapshot)}\n\n"

            while True:
                if await request.is_disconnected():
                    break

                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"event: {message.get('type', 'update')}\ndata: {json.dumps(message)}\n\n"
                except TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            websocket_manager.disconnect_sse(connection_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
