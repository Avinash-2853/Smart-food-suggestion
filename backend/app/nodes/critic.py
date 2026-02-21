import json
from langchain_core.prompts import ChatPromptTemplate
from app.state import AgentState
from app.ai.llm.gemini_client import gemini_client
from app.ai.prompts.templates import CRITIC_SYSTEM_PROMPT
from app.core.logger import logger
import time

async def qa_critic_node(state: AgentState):
    """
    Evaluates the current suggestions and menu draft against user constraints.
    """
    start_time = time.time()
    logger.info("🧐 Evaluating menu quality...")
    
    llm = gemini_client.get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", CRITIC_SYSTEM_PROMPT),
        ("human", "User Profile: {profile}\nMenu Draft: {draft}")
    ])
    
    chain = prompt | llm
    
    response = await chain.ainvoke({
        "profile": state["user_profile"],
        "draft": state["menu_draft"]
    })
    
    try:
        # Expected output: JSON with "approved": bool and "feedback": str
        content = response.content.replace("```json", "").replace("```", "").strip()
        evaluation = json.loads(content)
        duration = time.time() - start_time
        logger.info(f"✅ Evaluation result: {evaluation} (took {duration:.2f}s)")
    except Exception as e:
        logger.error(f"❌ Error in critic parsing: {e}")
        evaluation = {"approved": True, "feedback": "Auto-approved due to parsing error."}

    return {
        "approved": evaluation.get("approved", True),
        "critic_feedback": evaluation.get("feedback", ""),
        "error_reason": evaluation.get("feedback") if not evaluation.get("approved") else None
    }
