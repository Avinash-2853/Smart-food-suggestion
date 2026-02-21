from langchain_core.prompts import ChatPromptTemplate
from app.state import AgentState
from app.ai.llm.gemini_client import gemini_client
from app.ai.prompts.templates import GENERATOR_SYSTEM_PROMPT
from app.core.logger import logger

async def menu_generator_node(state: AgentState):
    """
    Formats the final menu for the user.
    """
    logger.info("✨ Generating final menu output...")
    
    llm = gemini_client.get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", GENERATOR_SYSTEM_PROMPT),
        ("human", "Profile: {profile}\nSuggestions: {suggestions}")
    ])
    
    chain = prompt | llm
    
    response = await chain.ainvoke({
        "profile": state["user_profile"],
        "suggestions": state["current_suggestions"]
    })
    
    return {
        "final_output": response.content
    }
