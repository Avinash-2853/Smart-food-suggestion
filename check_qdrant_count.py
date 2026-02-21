import asyncio
from qdrant_client import AsyncQdrantClient

async def check():
    try:
        q = AsyncQdrantClient(url='http://localhost:6333')
        collections = await q.get_collections()
        print(f"Collections: {collections}")
        for c in collections.collections:
            if c.name == "smart_food_menu":
                info = await q.get_collection(collection_name="smart_food_menu")
                print(f"Collection 'smart_food_menu' points count: {info.points_count}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
