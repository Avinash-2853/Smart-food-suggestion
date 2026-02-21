from sentence_transformers import SentenceTransformer
from app.state import AgentState
from app.database import db_manager
from app.core.constants import MENU_COLLECTION, EMBEDDING_MODEL
from app.core.logger import logger

# Initialize model once
model = SentenceTransformer(EMBEDDING_MODEL)

async def search_rag_node(state: AgentState):
    """
    Hybrid search node: SQL pre-filtering + Vector similarity search.
    """
    profile = state["user_profile"]
    logger.info(f"🔍 Searching for items matching profile: {profile}")
    
    # 1. Generate Query Vector
    query_text = profile.get("search_query") or state["user_query"]
    query_vector = model.encode(query_text).tolist()
    
    # 2. Vector Search with Qdrant (using basic metadata filters if present)
    # Note: For production, we'd add complex filters here
    search_results = await db_manager.qdrant_client.search(
        collection_name=MENU_COLLECTION,
        query_vector=query_vector,
        limit=10
    )
    
    suggestions = []
    for hit in search_results:
        suggestions.append(hit.payload)
    
    logger.info(f"✅ Found {len(suggestions)} semantic matches.")
    
    # 3. (Optional) Enhance with SQL data if needed, but payload already has most info
    
    return {
        "current_suggestions": suggestions,
        "menu_draft": f"Draft menu with {len(suggestions)} items based on your search for '{query_text}'."
    }
