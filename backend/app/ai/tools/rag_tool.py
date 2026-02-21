from langchain_core.tools import tool
from sentence_transformers import SentenceTransformer
from app.database import db_manager
from app.core.constants import MENU_COLLECTION, EMBEDDING_MODEL
from app.core.logger import logger
import asyncio

# Initialize model once
model = SentenceTransformer(EMBEDDING_MODEL)

@tool
def search_food_items(query: str, limit: int = 10):
    """
    Search for food items in the database based on a semantic query.
    Returns a list of matching food items with their details.
    """
    logger.info(f"🛠️ Tool: Searching for '{query}'...")
    
    # Generate vector
    query_vector = model.encode(query).tolist()
    
    # We use a wrapper for the async call since langchain tools are typically synchronous in this context or handled by the agent
    # However, since our db_manager is async, we use asyncio.run or better, make the tool async if the runner supports it.
    # LangChain's AgentExecutor/Graph can handle async tools.
    
    async def _search():
        search_results = await db_manager.qdrant_client.search(
            collection_name=MENU_COLLECTION,
            query_vector=query_vector,
            limit=limit
        )
        return [hit.payload for hit in search_results]

    try:
        # If already in an event loop (FastAPI), we need to handle this carefully
        import nest_asyncio
        nest_asyncio.apply()
    except:
        pass
        
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_search())
