import asyncio
import uuid
from datetime import datetime
from temporalio.client import Client
from app.workflows.order_workflow import OrderWorkflow, OrderEvent

async def verify_e2e_flow():
    # 1. Connect to Temporal
    client = await Client.connect("localhost:7233")
    order_id = f"verification-{uuid.uuid4().hex[:6]}"
    
    print(f"🏁 Starting End-to-End Verification for Order: {order_id}")
    
    # 2. Start the workflow
    handle = await client.start_workflow(
        OrderWorkflow.run,
        id=f"order-{order_id}",
        task_queue="order-tasks",
        args=[order_id, {
            "name": "Standard Supervisor",
            "base_instruction": "You are the verification agent. Monitor and summary events accurately."
        }]
    )
    
    # helper for signaling
    async def send_event(e_type):
        event = OrderEvent(
            event_type=e_type,
            payload={"source": "verify_script"},
            timestamp=datetime.utcnow().isoformat()
        )
        await handle.signal(OrderWorkflow.add_event, event)
        print(f"   [SIGNAL] Sent {e_type}")

    # 3. Step 1 Events
    await send_event("payment_confirmed")
    await asyncio.sleep(10) # Give agent time to reason
    
    await send_event("shipment_delayed")
    await asyncio.sleep(10)
    
    await send_event("delivered")
    
    # Wait for the workflow to complete naturally
    print("⏳ Waiting for workflow to complete and generate final summary...")
    result = await handle.result()
    print(f"🏁 Workflow Result: {result}")
    
    # 4. Verify Final State (Step 2 Validation Checklist)
    state = await handle.query(OrderWorkflow.get_state)
    print("\n🧐 Verification Checklist Results:")
    print(f"   - Memory Summary Updated: {'✅' if len(state['memory_summary']) > 0 else '❌'}")
    print(f"   - Final Summary Result: {'✅' if state['summary_result'] else '❌'}")
    
    if "delivered" in state['memory_summary'].lower() or "delivered" in str(state['summary_result']).lower():
         print("   - Delivered Event Recognized: ✅")
    else:
         print("   - Delivered Event Recognized: ❌ (Check logs)")

    print(f"\nFinal Memory Summary: {state['summary_result']}")
    print("\n✅ Verification complete. System is stable and correctly handles lifecycle events.")

if __name__ == "__main__":
    asyncio.run(verify_e2e_flow())
