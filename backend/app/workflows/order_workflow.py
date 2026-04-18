from datetime import timedelta
import asyncio
from typing import List, Optional
from temporalio import workflow
from pydantic import BaseModel

# --- Shared Type-Safe Models ---
class OrderEvent(BaseModel):
    event_id: Optional[str] = None
    event_type: str
    payload: dict
    timestamp: str

class ActionRecord(BaseModel):
    action: str
    action_input: Optional[str] = None
    timestamp: str
    success: bool = True
    error_msg: Optional[str] = None

class OrderState(BaseModel):
    order_id: str
    status: str = "pending"
    events: List[OrderEvent] = []
    memory_summary: str = ""
    next_wake_up: Optional[str] = None
    summary_result: Optional[str] = None
    supervisor_config: dict = {}
    extra_instructions: List[str] = []
    last_error: Optional[str] = None
    is_fallback_active: bool = False
    action_history: List[ActionRecord] = []
    termination_reason: Optional[str] = None

@workflow.defn
class OrderWorkflow:
    def __init__(self) -> None:
        self._state = OrderState(order_id="")
        self._exit = False
        self.sleep_duration = 60

    @workflow.run
    async def run(self, order_id: str, supervisor_config: dict = {}) -> str:
        self._state.order_id = order_id
        self._state.supervisor_config = supervisor_config
        
        workflow.logger.info(f"[ORDER:{order_id}] Initializing autonomous lifecycle. Core: {supervisor_config.get('name')}")
        
        from app.workflows.activities import execute_agent, call_tool
        
        loop_count = 0
        max_loops = 50 
        
        while not self._exit:
            loop_count += 1
            if loop_count > max_loops:
                self._state.termination_reason = "MAX_LOOPS_EXCEEDED"
                workflow.logger.error(f"[ORDER:{order_id}] Safety Termination: Exceeded max loop count.")
                break

            # Process evaluation cycle on every iteration (start, signal, or timer)
            if True:
                # 1. Atomic Event Capture
                events_to_process = list(self._state.events)
                current_state_dump = self._state.model_dump()
                current_state_dump["events"] = [e.model_dump() for e in events_to_process]
                
                workflow.logger.info(f"[ORDER:{order_id}] Loop {loop_count}: Synchronizing with agent.")
                
                try:
                    # Execute reasoning activity
                    decision_dict = await workflow.execute_activity(
                        execute_agent,
                        current_state_dump,
                        start_to_close_timeout=timedelta(minutes=2),
                    )
                    
                    # 2. State Resolution & Completion Check
                    processed_count = len(events_to_process)
                    self._state.events = self._state.events[processed_count:]
                    
                    # Deterministic Rule: End lifecycle if delivery finalized
                    completion_events = {"delivered", "order_delivered", "cancelled", "termination_approved"}
                    if any(e.event_type in completion_events for e in events_to_process):
                        workflow.logger.info(f"[ORDER:{order_id}] Finalization event detected. Initiating retrospective.")
                        self._state.termination_reason = "LIFECYCLE_COMPLETED"
                        self._exit = True

                    self._state.memory_summary = decision_dict.get("memory_update", self._state.memory_summary)
                    self._state.last_error = decision_dict.get("last_error")
                    self._state.is_fallback_active = decision_dict.get("is_fallback", False)
                    self.sleep_duration = decision_dict.get("sleep_for_seconds", 60)

                    # 3. Guarded Action Execution
                    if decision_dict.get("should_act") and decision_dict.get("action"):
                        action = decision_dict["action"]
                        if action == "close_workflow":
                            self._state.termination_reason = "AGENT_CLOSE"
                            self._exit = True
                        else:
                            # Loop Prevention Check
                            if self._is_stuck_in_loop(action, decision_dict.get("action_input")):
                                self._state.last_error = "ACTION_LOOP_DETECTED"
                                self._state.is_fallback_active = True
                                self.sleep_duration = 600
                                workflow.logger.warning(f"[ORDER:{order_id}] Suspected infinite loop detected for action '{action}'. Cooling down.")
                            else:
                                try:
                                    await workflow.execute_activity(
                                        call_tool,
                                        {
                                            "action": action,
                                            "action_input": decision_dict.get("action_input"),
                                            "order_id": order_id
                                        },
                                        start_to_close_timeout=timedelta(minutes=1),
                                    )
                                    self._log_action(action, decision_dict.get("action_input"), success=True)
                                except Exception as e:
                                    self._log_action(action, decision_dict.get("action_input"), success=False, error=str(e))
                
                except Exception as e:
                    workflow.logger.error(f"[ORDER:{order_id}] Reasoning activity failed: {e}")
                    self._state.last_error = f"ACTIVITY_FAILURE: {str(e)}"
                
                if self._exit:
                    break

            # 4. Deterministic Wait
            now = workflow.now()
            self._state.next_wake_up = (now + timedelta(seconds=self.sleep_duration)).isoformat()
            
            try:
                await workflow.wait_condition(
                    lambda: self._exit or len(self._state.events) > 0,
                    timeout=float(self.sleep_duration)
                )
            except asyncio.TimeoutError:
                pass
            
        # Final Retrospective
        try:
            final_decision = await workflow.execute_activity(
                execute_agent,
                {**self._state.model_dump(), "is_final": True, "termination_reason": self._state.termination_reason},
                start_to_close_timeout=timedelta(minutes=1),
            )
            self._state.summary_result = final_decision.get("memory_update", "Completion summary generated.")
        except:
            self._state.summary_result = "Workflow terminated. (Final reasoning summary unavailable)"

        workflow.logger.info(f"[ORDER:{order_id}] Lifecycle concluded. Reason: {self._state.termination_reason}")
        return f"Order {order_id} managed successfully."

    def _is_stuck_in_loop(self, action: str, action_input: Optional[str]) -> bool:
        consecutive = 0
        for record in reversed(self._state.action_history):
            if record.action == action and record.action_input == action_input:
                consecutive += 1
            else:
                break
        return consecutive >= 3

    def _log_action(self, action: str, action_input: Optional[str], success: bool, error: Optional[str] = None):
        self._state.action_history.append(ActionRecord(
            action=action,
            action_input=action_input,
            timestamp=workflow.now().isoformat(),
            success=success,
            error_msg=error
        ))
        # Keep history manageable
        if len(self._state.action_history) > 100:
            self._state.action_history.pop(0)

    @workflow.signal
    async def add_event(self, event: OrderEvent) -> None:
        if any(e.event_id == event.event_id for e in self._state.events if e.event_id):
            return
        self._state.events.append(event)

    @workflow.signal
    async def add_instruction(self, instruction: str) -> None:
        self._state.extra_instructions.append(instruction)

    @workflow.signal
    async def terminate(self) -> None:
        self._state.termination_reason = "USER_TERMINATED"
        self._exit = True

    @workflow.query
    def get_state(self) -> dict:
        return self._state.model_dump()
