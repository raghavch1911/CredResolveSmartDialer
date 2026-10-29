
from contextlib import asynccontextmanager
import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.database import init_db, get_db
from app.services.registry import create_agent, create_borrower
from app.services.dialer import ProgressiveDialer, AllocationError
from app.services.safety import SafetyController
from app.services.call_service import CallService
from app.services.pacing import PredictivePacingEngine
from app.services.events import process_provider_event
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CredResolve SmartDialer",
    description="A safety-first outbound dialing prototype.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

dialer = ProgressiveDialer()
safety = SafetyController()
call_service = CallService()
pacing_engine = PredictivePacingEngine()


class AgentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class BorrowerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=5, max_length=20)


class ProviderEventRequest(BaseModel):
    call_id: int = Field(gt=0)
    event_id: str = Field(min_length=1, max_length=200)
    event_type: str

@app.get("/")
def root():
    return {
        "message": "CredResolve SmartDialer API is running",
        "status": "ok",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/agents", status_code=201)
def add_agent(request: AgentRequest):
    try:
        return create_agent(request.name)
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/agents")
def list_agents():
    with get_db() as connection:
        rows = connection.execute(
            "SELECT * FROM agents ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]


@app.post("/borrowers", status_code=201)
def add_borrower(request: BorrowerRequest):
    try:
        return create_borrower(request.name, request.phone)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="A borrower with this phone number already exists",
        )


@app.get("/borrowers")
def list_borrowers():
    with get_db() as connection:
        rows = connection.execute(
            "SELECT * FROM borrowers ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]


@app.post("/dial/allocate")
def allocate_call():
    try:
        return dialer.allocate_call()
    except AllocationError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.post("/safety/evaluate")
def evaluate_safety(requested: int, provider_healthy: bool = True):
    decision = safety.evaluate(requested, provider_healthy)
    return {
        "requested": decision.requested,
        "approved": decision.approved,
        "reason": decision.reason,
    }


@app.post("/calls/initiate")
def initiate_call(provider: str = "mock_a"):
    try:
        return call_service.initiate(provider)
    except AllocationError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except TimeoutError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/calls")
def list_calls():
    with get_db() as connection:
        rows = connection.execute(
            "SELECT * FROM calls ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]


@app.post("/dial/predictive")
def predictive_dial(
    answer_rate: float = 0.5,
    provider_healthy: bool = True,
    provider: str = "mock_a",
    max_batch: int = 10,
):
    if not 0 < answer_rate <= 1:
        raise HTTPException(
            status_code=422,
            detail="answer_rate must be greater than 0 and at most 1",
        )

    if not 1 <= max_batch <= 50:
        raise HTTPException(
            status_code=422,
            detail="max_batch must be between 1 and 50",
        )

    with get_db() as connection:
        available = connection.execute(
            "SELECT COUNT(*) FROM agents WHERE status = 'AVAILABLE'"
        ).fetchone()[0]

        active = connection.execute(
            """
            SELECT COUNT(*) FROM calls
            WHERE status IN ('INITIATED', 'RINGING', 'ANSWERED', 'CONNECTED')
            """
        ).fetchone()[0]

        ringing = connection.execute(
            "SELECT COUNT(*) FROM calls WHERE status = 'RINGING'"
        ).fetchone()[0]

    recommendation = pacing_engine.recommend(
        available_agents=available,
        active_calls=active,
        answer_rate=answer_rate,
        provider_healthy=provider_healthy,
        ringing_calls=ringing,
        max_batch=max_batch,
    )

    decision = safety.evaluate(
        recommendation.requested_calls,
        provider_healthy=provider_healthy,
    )

    results = []

    for _ in range(decision.approved):
        try:
            results.append(call_service.initiate(provider))
        except (AllocationError, TimeoutError) as exc:
            results.append({"error": str(exc)})
            # Stop the batch when capacity or provider reliability
            # becomes uncertain.
            break

    return {
        "pacing_requested": recommendation.requested_calls,
        "safety_approved": decision.approved,
        "safety_reason": decision.reason,
        "answer_rate": recommendation.answer_rate,
        "available_agents_at_start": recommendation.available_agents,
        "active_calls_at_start": recommendation.active_calls,
        "pacing_reason": recommendation.reason,
        "initiated_results": results,
    }


@app.post("/provider/events")
def provider_event(request: ProviderEventRequest):
    try:
        return process_provider_event(
            call_id=request.call_id,
            event_id=request.event_id,
            event_type=request.event_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/agents/{agent_id}/available")
def make_agent_available(agent_id: int):
    with get_db() as connection:
        result = connection.execute(
            """
            UPDATE agents
            SET status = 'AVAILABLE', reserved_at = NULL
            WHERE id = ? AND status IN ('WRAP_UP', 'PAUSED', 'OFFLINE')
            """,
            (agent_id,),
        )

        if result.rowcount != 1:
            raise HTTPException(
                status_code=409,
                detail="Agent not found or cannot transition to AVAILABLE",
            )

    return {"agent_id": agent_id, "status": "AVAILABLE"}


@app.get("/providers/health")
def providers_health():
    return call_service.provider_health()