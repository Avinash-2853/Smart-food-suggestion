import json
import time
from langchain_core.prompts import ChatPromptTemplate
from app.state import AgentState
from app.ai.llm.gemini_client import gemini_client
from app.ai.prompts.templates import PROFILER_SYSTEM_PROMPT
from app.core.logger import logger
from app.ai.tools.rag_tool import search_food_items

async def user_profiler_node(state: AgentState):
    """
    Profiler agent that uses RAG tool and handles feedback from Critic.
    """
    start_time = time.time()
    logger.info(f"🧠 Profiler Agent started for query: {state['user_query']}")
    
    llm = gemini_client.get_llm()
    
    # Bind the tool to the LLM
    llm_with_tools = llm.bind_tools([search_food_items])
    
    # Prepare the context (including feedback if any)
    feedback_context = ""
    if state.get("critic_feedback"):
        feedback_context = f"\n\nREVISION_FEEDBACK FROM CRITIC: {state['critic_feedback']}"
        logger.info(f"🔄 Profiler received feedback: {state['critic_feedback']}")

    prompt = ChatPromptTemplate.from_messages([
        ("system", PROFILER_SYSTEM_PROMPT),
        ("human", "User Query: {query}{feedback}")
    ])
    
    # We'll use a simple loop for tool calling
    messages = prompt.format_messages(query=state["user_query"], feedback=feedback_context)
    
    # 1. First call to LLM
    response = await llm_with_tools.ainvoke(messages)
    messages.append(response)
    
    # 2. Check for tool calls and execute
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "search_food_items":
                tool_result = search_food_items.invoke(tool_call["args"])
                # Add tool response to messages
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result),
                    "tool_call_id": tool_call["id"]
                })
        
        # 3. Final call to get the structured JSON output
        response = await llm_with_tools.ainvoke(messages)
        content = response.content
    else:
        content = response.content

    # Parse the final JSON from content
    try:
        content_clean = content.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(content_clean)
        
        # Extract profile and items
        profile = {
            "budget": result_json.get("budget"),
            "party_size": result_json.get("party_size", 1),
            "dietary_tags": result_json.get("dietary_tags", []),
            "cuisine_preferences": result_json.get("cuisine_preferences", []),
            "has_health_goal": result_json.get("has_health_goal", False),
            "location": result_json.get("location"),
            "search_query": result_json.get("search_query")
        }
        items = result_json.get("selected_items", [])
        
    except Exception as e:
        logger.error(f"❌ Error parsing Profiler Agent JSON: {e}")
        # Fallback
        profile = state.get("user_profile", {})
        items = state.get("current_suggestions", [])

    duration = time.time() - start_time
    logger.info(f"✅ Profiler complete in {duration:.2f}s with {len(items)} items.")

    return {
        "user_profile": profile,
        "current_suggestions": items,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "critic_feedback": None # Reset feedback after handling
    }
