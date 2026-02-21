from langchain_core.tools import tool
from sentence_transformers import SentenceTransformer
from app.database import db_manager
from app.core.constants import MENU_COLLECTION, EMBEDDING_MODEL
from app.core.logger import logger
import asyncio

# Initialize model once
model = SentenceTransformer(EMBEDDING_MODEL)

@tool
async def search_food_items(query: str, limit: int = 10):
    """
    Retrieves raw 'menu chunks' (food items) from the restaurant database. 
    
    The tool takes a search query, uses semantic vector similarity to find the most relevant 
    dishes, and returns them as a list of data chunks. 
    
    Each chunk (food item) contains: itemName, price, description, proteinG, calories, and restaurantName.
    
    The Profiler Agent must use these retrieved chunks to evaluate if they match the user's 
    intent and constraints before finalizing the menu.
    """
    logger.info(f"🛠️ Tool: Searching for '{query}'...")
    
    # Generate vector
    # model.encode is a synchronous CPU-bound operation
    # For high performance, we could wrap it in run_in_executor
    query_vector = model.encode(query).tolist()
    
    search_results = await db_manager.qdrant_client.search(
        collection_name=MENU_COLLECTION,
        query_vector=query_vector,
        limit=limit
    )
    return [hit.payload for hit in search_results]
