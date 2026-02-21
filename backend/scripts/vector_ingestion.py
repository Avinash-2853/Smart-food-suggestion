import asyncio
import json
import os
import sys

import asyncpg
from dotenv import load_dotenv
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Load environment variables from .env
load_dotenv()

# Retrieve connection URLs from environment 
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@db:5432/smart_food")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

COLLECTION_NAME = "smart_food_menu"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384


def format_text_chunk(item: dict) -> str:
    """Format the relational SQL data into a highly descriptive semantic text string."""
    
    # Safely load JSON strings for nutrition
    nutritional_info = item.get("nutritional_info") or "{}"
    if isinstance(nutritional_info, str):
        try:
            ni = json.loads(nutritional_info)
            macros = f"{ni.get('calories', '0')} Cals, {ni.get('protein_g', '0')}g Protein, {ni.get('fat_g', '0')}g Fat, {ni.get('carbs_g', '0')}g Carbs"
        except:
            macros = "None available"
    else:
        macros = "None available"

    desc = item.get("description") if item.get("description") else "No description provided."
    rest_desc = item.get("restaurant_description") if item.get("restaurant_description") else "No restaurant description provided."
    dietary_tags = ", ".join(item.get("dietary_tags", [])) if item.get("dietary_tags") else "None"
    allergens = ", ".join(item.get("allergens", [])) if item.get("allergens") else "None"
    keywords = ", ".join(item.get("search_keywords", [])) if item.get("search_keywords") else "None"

    # Construct the highly descriptive semantic paragraph for the LLM Embedding
    text_chunk = (
        f"Item Name: {item['name']}. "
        f"Category: {item.get('category_name')} from the {item.get('menu_type')} menu. "
        f"Served at Restaurant: {item.get('restaurant_name')}, which specializes in {', '.join(item.get('cuisine_types', []))} cuisine. "
        f"Restaurant Overview: {rest_desc}. "
        f"Restaurant Location: {item.get('address')}. "
        f"Item Description: {desc} "
        f"Price: ${item['price']}. "
        f"Dietary Tags: {dietary_tags}. "
        f"Allergens: {allergens}. "
        f"Nutritional Data: {macros}. "
        f"Rating: {item.get('rating_average', 0)}/5 from {item.get('rating_count', 0)} reviews. "
        f"Search keywords: {keywords}."
    )
    return text_chunk


async def generate_and_store_embeddings():
    print(f"🔌 Connecting to PostgreSQL DB...")
    
    # Wait for PostgreSQL
    conn = None
    for i in range(10):
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            break
        except Exception as e:
            print(f"Database not ready yet... Retrying in 5s")
            await asyncio.sleep(5)

    if not conn:
        print("❌ Could not connect to PostgreSQL after 10 attempts.")
        return

    # Wait for Qdrant
    print(f"🔌 Connecting to Qdrant Vector DB...")
    qdrant = AsyncQdrantClient(url=QDRANT_URL)
    
    for i in range(10):
        try:
            await qdrant.get_collections()
            break
        except Exception as e:
            print(f"Qdrant not ready yet... Retrying in 5s")
            await asyncio.sleep(5)

    try:
        # Load embedding model using HuggingFace
        print(f"🧠 Loading Sentence Transformer Model: {EMBEDDING_MODEL_NAME}...")
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)

        # Ensure Qdrant Collection exists
        collections = await qdrant.get_collections()
        exists = any(c.name == COLLECTION_NAME for c in collections.collections)
        
        if not exists:
            print(f"🏗️ Creating Qdrant Collection: {COLLECTION_NAME}")
            await qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=EMBEDDING_DIMENSIONS, distance=Distance.COSINE),
            )
        else:
            print(f"⚠️ Collection {COLLECTION_NAME} already exists. Skipping ingestion to avoid duplicates.")
            # return # Uncomment to prevent re-running if exists

        # Fetch the giant JOIN statement
        print("🔍 Querying joined relational data from PostgreSQL...")
        query = """
        SELECT 
            m.id as menu_item_id, m.name, m.description, m.price, m.category, m.search_keywords, 
            m.rating_average, m.rating_count, m.allergens, m.nutritional_info, m.dietary_tags, m.menu_type,
            r.id as restaurant_id, r.name as restaurant_name, r.description as restaurant_description, 
            r.cuisine_types, r.address,
            c.name as category_name
        FROM menu_items m
        INNER JOIN restaurants r ON m.restaurant_id = r.id
        LEFT JOIN menu_categories c ON m.category_id = c.id
        """
        records = await conn.fetch(query)
        print(f"✅ Fetched {len(records)} rows from PostgreSQL.")

        # Process in batches
        BATCH_SIZE = 100
        total_inserted = 0
        
        for i in range(0, len(records), BATCH_SIZE):
            batch_records = records[i:i + BATCH_SIZE]
            
            payloads = []
            text_chunks = []
            vectors = []
            points = []

            for row in batch_records:
                row_dict = dict(row)
                
                # Format the text chunk
                chunk = format_text_chunk(row_dict)
                text_chunks.append(chunk)
                
                # Cleanup metadata payload for fast SQL-like filtering in VectorDB
                payload = {
                    "menu_item_id": str(row_dict["menu_item_id"]),
                    "restaurant_id": str(row_dict["restaurant_id"]),
                    "restaurant_name": row_dict["restaurant_name"],
                    "price": float(row_dict["price"]),
                    "rating_average": float(row_dict["rating_average"]),
                    "menu_type": row_dict["menu_type"],
                    "dietary_tags": row_dict.get("dietary_tags", []),
                    "search_keywords": row_dict.get("search_keywords", []),
                    "text_chunk": chunk  # We store the raw text here so the LLM can read it later 
                }
                payloads.append(payload)

            # Generate Embeddings internally using Sentence Transformers
            print(f"⚡ Generating embeddings for batch {i // BATCH_SIZE + 1}...")
            embeddings = model.encode(text_chunks, convert_to_numpy=True).tolist()
            
            # Construct Qdrant Points
            for j, payload in enumerate(payloads):
                points.append(
                    PointStruct(
                        id=payload["menu_item_id"], # Link the vector UUID to the postgres UUID
                        vector=embeddings[j],
                        payload=payload
                    )
                )

            # Push to Qdrant
            await qdrant.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            total_inserted += len(points)
            print(f"  Inserted batch {i // BATCH_SIZE + 1}: {len(points)} items")

        print(f"✅ Successfully vectorized and stored {total_inserted} chunks into Qdrant!")

    except Exception as e:
        print(f"❌ Error during RAG injection: {e}", file=sys.stderr)
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(generate_and_store_embeddings())
