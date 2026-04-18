import asyncio
import signal
import logging
from temporalio.client import Client
from temporalio.worker import Worker, UnsandboxedWorkflowRunner
from app.core.config import settings
from app.workflows.order_workflow import OrderWorkflow
from app.workflows.activities import execute_agent, call_tool
from app.db.database import engine

# --- Professional Telemetry ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Aegis-Worker")

async def preflight_checks():
    """Verify system readiness before engaging tasks."""
    logger.info("Engaging pre-flight diagnostics...")
    
    # 1. Verify Database
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[DIAGNOSTIC] Database: CONNECTED")
    except Exception as e:
        logger.error(f"[DIAGNOSTIC] Database: FAILED | {e}")
        return False

    # 2. Verify LLM Config (OpenRouter)
    if not settings.OPENROUTER_API_KEY:
        logger.warning("[DIAGNOSTIC] OpenRouter: API Key Missing (Failover required)")
    else:
        logger.info("[DIAGNOSTIC] OpenRouter: CONFIGURED")

    return True

async def main():
    if not await preflight_checks():
        logger.error("Pre-flight checks failed. Aborting startup.")
        return

    try:
        # Step 4: Robust Connection Handling
        client = await Client.connect(
            settings.TEMPORAL_HOST, 
            namespace=settings.TEMPORAL_NAMESPACE
        )

        worker = Worker(
            client,
            task_queue="order-tasks",
            workflows=[OrderWorkflow],
            activities=[execute_agent, call_tool],
            workflow_runner=UnsandboxedWorkflowRunner(),
        )

        logger.info("Worker synchronized. Ready for autonomous missions.")
        
        # Graceful shutdown handler
        stop_event = asyncio.Event()

        def handle_interrupt():
            logger.info("Shutdown signal received. Cleaving connections...")
            stop_event.set()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, handle_interrupt)
            except NotImplementedError:
                # Windows fallback
                pass

        await worker.run()
        
    except Exception as e:
        logger.error(f"Critical Worker Failure: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
