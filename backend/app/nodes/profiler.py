import json
from langchain_core.prompts import ChatPromptTemplate
from app.state import AgentState
from app.ai.llm.gemini_client import gemini_client
from app.ai.prompts.templates import PROFILER_SYSTEM_PROMPT
from app.core.logger import logger

import time

async def user_profiler_node(state: AgentState):
    """
    Extracts structured constraints from the user query using Gemini.
    """
    start_time = time.time()
    logger.info(f"🧠 Profiling user query: {state['user_query']}")
    
    llm = gemini_client.get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", PROFILER_SYSTEM_PROMPT),
        ("human", "{query}")
    ])
    
    chain = prompt | llm
    
    response = await chain.ainvoke({"query": state["user_query"]})
    
    try:
        # Clean response content for JSON parsing
        content = response.content.replace("```json", "").replace("```", "").strip()
        profile = json.loads(content)
        logger.info(f"✅ Extracted profile: {profile}")
    except Exception as e:
        logger.error(f"❌ Error parsing profile: {e}")
        profile = {
            "budget": None,
            "party_size": 1,
            "dietary_tags": [],
            "cuisine_preferences": [],
            "has_health_goal": False,
            "location": None,
            "search_query": state["user_query"]
        }

    duration = time.time() - start_time
    logger.info(f"✅ Profiling complete in {duration:.2f}s")

    return {
        "user_profile": profile,
        "iteration_count": state.get("iteration_count", 0) + 1
    }
