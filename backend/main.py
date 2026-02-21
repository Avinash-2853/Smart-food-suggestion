import asyncio
from dotenv import load_dotenv
from app.graph import food_graph
from app.database import db_manager
from app.core.logger import logger

load_dotenv()

async def main():
    # 1. Initialize DB connections
    logger.info("🚀 Starting Smart Food Suggestion System...")
    await db_manager.connect()
    
    # 2. Define Initial State
    query = "I need high-protein vegan meals for 2 people with a budget of $50."
    initial_state = {
        "user_query": query,
        "iteration_count": 0,
        "approved": False
    }
    
    # 3. Execute the Graph
    print(f"\n--- 📝 User Query: {query} ---\n")
    
    async for output in food_graph.astream(initial_state):
        for key, value in output.items():
            print(f"\n[Node: {key}]")
            # print(f"Value: {value}") # Too verbose for full state
            
    # 4. Final Output
    final_state = await food_graph.ainvoke(initial_state)
    print("\n--- 🥗 Final Menu Recommendation ---\n")
    print(final_state["final_output"])
    
    # 5. Cleanup
    await db_manager.disconnect()
    logger.info("💤 System shut down.")

if __name__ == "__main__":
    asyncio.run(main())
