import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "")
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
QDRANT_URL: str = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
OPEN_ROUTER_API_KEY: str = os.getenv("OPEN_ROUTER_API_KEY", "")
