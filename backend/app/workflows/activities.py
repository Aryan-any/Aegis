from temporalio import activity
from app.agent.runtime import run_agent
from app.services.action_service import action_service

ALLOWED_ACTIONS = {
    "message_fulfillment_team",
    "message_payments_team",
    "message_logistics_team",
    "message_customer",
    "create_internal_note",
    "close_workflow"
}

@activity.defn
async def execute_agent(state_dict: dict) -> dict:
    """
    Orchestrates the LLM reasoning loop.
    This activity is idempotent and retriable by the workflow.
    """
    try:
        activity.logger.info(f"Agent reasoning initiated for Order: {state_dict.get('order_id')}")
        decision = await run_agent(state_dict)
        
        # Guardrail: Runtime validation of action names
        if decision.action and decision.action not in ALLOWED_ACTIONS:
            activity.logger.warning(f"Guardrail Rejection: Agent attempted restricted action '{decision.action}'")
            decision.should_act = False
            decision.action = None
            
        return decision.model_dump()
    except Exception as e:
        activity.logger.error(f"Agent Reasoning Failed: {str(e)}")
        raise e

@activity.defn
async def call_tool(data: dict) -> str:
    """
    Executes a concrete tool action via the ActionService.
    """
    try:
        action = data.get("action")
        action_input = data.get("action_input")
        order_id = data.get("order_id")
        
        if not action or action not in ALLOWED_ACTIONS:
            raise ValueError(f"Invalid or unauthorized action: {action}")

        activity.logger.info(f"Dispatching Tool: {action}")
        
        # Delegate to Service Layer
        result = await action_service.execute(order_id, action, action_input)
        return result
        
    except Exception as e:
        activity.logger.error(f"Tool Execution Critical Failure: {str(e)}")
        raise e
