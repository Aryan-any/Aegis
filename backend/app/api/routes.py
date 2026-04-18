from fastapi import APIRouter, HTTPException, Depends, Request
from temporalio.client import Client
from app.core.config import settings
from app.workflows.order_workflow import OrderWorkflow, OrderEvent
from app.db.database import get_session, log_event, ActionLog, OrderTimeline
from sqlmodel import Session, select
import uuid
import logging
import json
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api")
logger = logging.getLogger("SagePilot-API")

# --- Models ---
class CreateRunRequest(BaseModel):
    order_id: Optional[str] = None
    supervisor_type: str = "standard"

class EventRequest(BaseModel):
    event_type: str
    payload: dict = Field(default_factory=dict)

class InstructionRequest(BaseModel):
    instruction: str

# --- Helpers ---
async def get_temporal_client():
    try:
        return await Client.connect(settings.TEMPORAL_HOST, namespace=settings.TEMPORAL_NAMESPACE)
    except Exception as e:
        logger.error(f"Failed to connect to Temporal: {e}")
        raise HTTPException(status_code=503, detail="Temporal server unreachable")

def get_full_id(order_id: str) -> str:
    return f"order-{order_id}" if not order_id.startswith("order-") else order_id

# --- Routes ---

@router.get("/runs")
async def list_runs():
    client = await get_temporal_client()
    try:
        runs = []
        async for workflow in client.list_workflows('WorkflowType = "OrderWorkflow"'):
            runs.append({
                "workflow_id": workflow.id,
                "status": str(workflow.status),
                "start_time": workflow.start_time.isoformat()
            })
        return runs
    except Exception as e:
        logger.error(f"Error listing runs: {e}")
        return []

@router.post("/runs")
async def start_run(req: CreateRunRequest):
    order_id = req.order_id or str(uuid.uuid4())
    client = await get_temporal_client()
    
    config = settings.SUPERVISOR_TEMPLATES.get(req.supervisor_type, settings.SUPERVISOR_TEMPLATES["standard"])
    
    try:
        handle = await client.start_workflow(
            OrderWorkflow.run,
            id=get_full_id(order_id),
            task_queue="order-tasks",
            args=[order_id, config]
        )
        return {"workflow_id": handle.id, "run_id": handle.run_id, "order_id": order_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/runs/{order_id}")
async def get_run_status(order_id: str):
    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(get_full_id(order_id))
        state = await handle.query(OrderWorkflow.get_state)
        return state
    except Exception as e:
        raise HTTPException(status_code=404, detail="Workflow not found")

@router.post("/runs/{order_id}/events")
async def send_event(order_id: str, req: EventRequest):
    client = await get_temporal_client()
    try:
        event = OrderEvent(
            event_id=str(uuid.uuid4()),
            event_type=req.event_type,
            payload=req.payload,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Log to DB using centralized logic
        log_event(order_id, req.event_type, json.dumps(req.payload))
        
        handle = client.get_workflow_handle(get_full_id(order_id))
        await handle.signal(OrderWorkflow.add_event, event)
        return {"status": "event sent", "event": event}
    except Exception as e:
        logger.error(f"Error sending event: {e}")
        raise HTTPException(status_code=404, detail="Workflow not found or error sending signal")

@router.get("/runs/{order_id}/timeline")
async def get_timeline(order_id: str, session: Session = Depends(get_session)):
    statement = select(OrderTimeline).where(OrderTimeline.order_id == order_id).order_by(OrderTimeline.created_at.asc())
    results = session.exec(statement).all()
    return results

@router.get("/runs/{order_id}/actions")
async def get_actions(order_id: str, session: Session = Depends(get_session)):
    statement = select(ActionLog).where(ActionLog.order_id == order_id).order_by(ActionLog.created_at.asc())
    results = session.exec(statement).all()
    return results

@router.post("/runs/{order_id}/terminate")
async def terminate_run(order_id: str):
    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(get_full_id(order_id))
        await handle.signal(OrderWorkflow.terminate)
        return {"status": "termination signal sent"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Workflow not found")

@router.post("/runs/{order_id}/instructions")
async def add_instruction(order_id: str, req: InstructionRequest):
    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(get_full_id(order_id))
        await handle.signal(OrderWorkflow.add_instruction, req.instruction)
        return {"status": "instruction added"}
    except Exception as e:
        logger.error(f"Error adding instruction: {e}")
        raise HTTPException(status_code=404, detail="Workflow not found or error adding instruction")

@router.post("/runs/{order_id}/pause")
async def pause_run(order_id: str):
    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(get_full_id(order_id))
        await handle.pause()
        return {"status": "workflow paused"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Workflow not found")

@router.post("/runs/{order_id}/resume")
async def resume_run(order_id: str):
    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(get_full_id(order_id))
        await handle.unpause()
        return {"status": "workflow resumed"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Workflow not found")

@router.get("/supervisors")
async def list_supervisors():
    return settings.SUPERVISOR_TEMPLATES
