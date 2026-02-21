from langgraph.graph import StateGraph, START, END
from app.state import AgentState
from app.nodes.profiler import user_profiler_node
from app.nodes.search import search_rag_node
from app.nodes.critic import qa_critic_node
from app.nodes.generator import menu_generator_node

def router(state: AgentState):
    """
    Decides whether to finalize the menu or go back to search for more items.
    """
    if state["approved"] or state["iteration_count"] >= 3:
        return "generator"
    return "search"

def create_food_suggestion_graph():
    # Initialize the graph with the state schema
    workflow = StateGraph(AgentState)

    # 1. Add Nodes
    workflow.add_node("profiler", user_profiler_node)
    workflow.add_node("search", search_rag_node)
    workflow.add_node("critic", qa_critic_node)
    workflow.add_node("generator", menu_generator_node)

    # 2. Define Edges (The hard-wired flow)
    workflow.add_edge(START, "profiler")
    workflow.add_edge("profiler", "search")
    workflow.add_edge("search", "critic")
    
    # 3. Add Conditional Edges (The intelligent loop)
    workflow.add_conditional_edges(
        "critic",
        router,
        {
            "generator": "generator",
            "search": "search"
        }
    )
    
    workflow.add_edge("generator", END)

    # Compile the graph
    return workflow.compile()

# Singleton instance of the graph
food_graph = create_food_suggestion_graph()
