# Implementation Plan: Data Processing & RAG Pipeline

To enable the AI agents to intelligently search and suggest food, we will build a Retrieval-Augmented Generation (RAG) tool. This involves moving our raw CSV data into a structured format and then creating searchable vector embeddings.

The pipeline will be executed in the following phases:

## Phase 1: Relational Database Setup & Data Ingestion
First, we need a robust backend to store the structured relationships between restaurants, categories, and menu items.

1. **Database Selection:** Choose a relational database (e.g., PostgreSQL or SQLite for local development).
2. **Schema Creation:** 
   - `Restaurants` table.
   - `Categories` table.
   - `Menu_Items` table (with Foreign Keys linking to Restaurants and Categories).
3. **Data Dumping:** Write a Python script (using Pandas and SQLAlchemy) to clean the data from `df_restaurants.csv`, `df_menu_categories.csv`, and `df_menuitems.csv` and dump it into the relational database.

## Phase 2: Text Chunk Generation
Vector databases require contextual text. We need to convert our relational data into descriptive text entries that an LLM can understand.

1. **Query Data:** Write a script to join the database tables.
2. **Text Formatting:** For each menu item, generate a comprehensive text chunk. 
   - *Example Formulation:* "At [Restaurant Name], which serves [Cuisine Type], we offer a [Category Name] item called [Menu Item Name]. Description: [Item Description]. It costs $[Price]. Dietary tags: [Tags]. Nutritional Info: [Macros]."

## Phase 3: Embedding and Vector Database Storage
Once we have our descriptive texts, we can vectorize them for semantic search.

1. **Vector DB Selection:** Choose a vector database (e.g., ChromaDB, Milvus, Qdrant, or Pinecone).
2. **Embedding Model:** Select an embedding model (e.g., OpenAI's `text-embedding-3-small` or an open-source model like `all-MiniLM-L6-v2` via Hugging Face).
3. **Generate Embeddings:** Pass the formatted text chunks through the embedding model to generate numerical vectors.
4. **Store Data:** Insert the generated text, metadata (like `restaurant_id`, `price`, `nutritional_info` for hard filtering), and the embed vectors into the Vector Database.

## Phase 4: RAG Tool Creation
Create the actual tool that the `AI Search Agent` will use.

1. **Search Function:** Build a Python tool that accepts natural language queries.
2. **Hybrid Search:** Implement a two-step search process:
   - *Semantic Search:* "Find me a vegan party platter" (Vector similarity).
   - *Metadata Filtering:* Ensure items returned match budget constraints or specific dietary tags using metadata.
3. **Tool Integration:** Wrap this function as a LangChain/CrewAI/AutoGen tool so the agents can call it autonomously.
