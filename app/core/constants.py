import os

# Database Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5433/smart_food")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")

# Collection Names
MENU_COLLECTION = "smart_food_menu"

# AI Model Configuration
GEMINI_MODEL = "gemini-flash-latest"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Search Defaults
DEFAULT_BATCH_SIZE = 100
MAX_AGENT_ITERATIONS = 3
