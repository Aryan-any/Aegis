import os
from pydantic_settings import BaseSettings
from typing import Dict, Any

class Settings(BaseSettings):
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    GOOGLE_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "minimax/minimax-m2.5:free"
    DATABASE_URL: str = "sqlite:///./sagepilot.db"
    ALLOWED_ORIGINS: str = "*"

    # Agent Templates moved from main.py
    SUPERVISOR_TEMPLATES: Dict[str, Any] = {
        "standard": {
            "name": "Standard Supervisor",
            "base_instruction": "You are an Order Supervisor Agent. Your job is to monitor the state of an order and decide on the next best action."
        },
        "aggressive": {
            "name": "Aggressive Logistician",
            "base_instruction": "You are a highly proactive logistics specialist. You prioritize speed and immediate problem resolution. You over-communicate with the logistics team and escalate issues at the first sign of delay."
        },
        "cautious": {
            "name": "Patient Customer Success",
            "base_instruction": "You are a customer-first success agent. You are patient and prioritize customer satisfaction. You always check with the customer before taking any major logistics actions."
        }
    }

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
