from typing import Optional, List, Generator
from sqlmodel import Field, SQLModel, create_engine, Session, select
from datetime import datetime
from app.core.config import settings
from sqlalchemy import text

class ActionLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: str
    action: str
    action_input: str
    status: str = "completed"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OrderTimeline(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: str
    event_type: str
    payload: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Engine configured with standard connection pooling
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    pool_pre_ping=True
)

def create_db_and_tables():
    """Initialize schema and database optimizations."""
    SQLModel.metadata.create_all(engine)
    if "sqlite" in settings.DATABASE_URL:
        # WAL mode is critical for concurrent access in Temporal activities
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.commit()

def get_session() -> Generator[Session, None, None]:
    """Dependency injection session provider."""
    with Session(engine) as session:
        yield session

def log_action(order_id: str, action: str, action_input: str):
    """Direct logging utility for Temporal activities."""
    with Session(engine) as session:
        log = ActionLog(order_id=order_id, action=action, action_input=action_input)
        session.add(log)
        session.commit()

def log_event(order_id: str, event_type: str, payload_str: str):
    """Direct logging utility for external event capture."""
    with Session(engine) as session:
        event = OrderTimeline(order_id=order_id, event_type=event_type, payload=payload_str)
        session.add(event)
        session.commit()
