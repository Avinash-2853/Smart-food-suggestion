import asyncpg
from qdrant_client import AsyncQdrantClient
from app.core.constants import DATABASE_URL, QDRANT_URL

class DatabaseManager:
    def __init__(self):
        self.pg_pool = None
        self.qdrant_client = AsyncQdrantClient(url=QDRANT_URL)

    async def connect(self):
        if not self.pg_pool:
            self.pg_pool = await asyncpg.create_pool(DATABASE_URL)
        return self.pg_pool

    async def disconnect(self):
        if self.pg_pool:
            await self.pg_pool.close()

db_manager = DatabaseManager()
