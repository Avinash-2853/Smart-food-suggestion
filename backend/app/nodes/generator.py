import json
from langchain_core.prompts import ChatPromptTemplate
from app.state import AgentState
from app.ai.llm.gemini_client import gemini_client
from app.ai.prompts.templates import GENERATOR_SYSTEM_PROMPT
from app.core.logger import logger
import time

async def menu_generator_node(state: AgentState):
    """
    Formats the final menu for the user as structured JSON.
    """
    start_time = time.time()
    logger.info("✨ Generating final structured menu output...")
    
    llm = gemini_client.get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", GENERATOR_SYSTEM_PROMPT),
        ("human", "User Query: {query}\nProfile: {profile}\nFiltered Suggestions: {suggestions}")
    ])
    
    chain = prompt | llm
    
    response = await chain.ainvoke({
        "query": state["user_query"],
        "profile": state["user_profile"],
        "suggestions": state["current_suggestions"]
    })
    
    content = response.content
    
    # Try to parse JSON from the response
    try:
        # Simple cleanup if LLM adds markdown triple backticks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        structured_data = json.loads(content)
        duration = time.time() - start_time
        logger.info(f"✅ Final menu generated in {duration:.2f}s")
        return {
            "final_output": structured_data.get("summary", ""),
            "structured_output": structured_data
        }
    except Exception as e:
        logger.error(f"❌ Failed to parse generator JSON: {str(e)}")
        return {
            "final_output": response.content,
            "structured_output": {"summary": response.content, "items": [], "error": "JSON parse error"}
        }
