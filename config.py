"""
Configuration for Project AETHER
"""

import os
from llm.llm_client import LLMProvider

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "huggingface").lower()
LLM_MODEL = os.getenv("LLM_MODEL", None)  # Model-specific, defaults handled in client

# API Configuration
API_HOST = os.getenv("HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", 8000))

# History Configuration
HISTORY_DB_PATH = os.getenv("HISTORY_DB_PATH", "aether_history.db")
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", 50))

# Frontend Configuration
FRONTEND_PATH = os.getenv("FRONTEND_PATH", "frontend")

