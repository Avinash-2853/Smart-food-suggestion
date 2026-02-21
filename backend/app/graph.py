from langgraph.graph import StateGraph, START, END
from app.state import AgentState
from app.nodes.profiler import user_profiler_node
from app.nodes.critic import qa_critic_node
from app.nodes.generator import menu_generator_node

def router(state: AgentState):
    """
    Decides whether to finalize the menu or go back to search for more items.
    """
    if state["approved"] or state["iteration_count"] >= 3:
        return "generator"
    return "profiler"

def create_food_suggestion_graph():
    # Initialize the graph with the state schema
    workflow = StateGraph(AgentState)

    # 1. Add Nodes
    workflow.add_node("profiler", user_profiler_node)
    workflow.add_node("critic", qa_critic_node)
    workflow.add_node("generator", menu_generator_node)

    # 2. Define Edges
    workflow.add_edge(START, "profiler")
    workflow.add_edge("profiler", "critic")
    
    # 3. Add Conditional Edges
    workflow.add_conditional_edges(
        "critic",
        router,
        {
            "generator": "generator",
            "profiler": "profiler"
        }
    )
    
    workflow.add_edge("generator", END)

    # Compile the graph
    return workflow.compile()

# Singleton instance of the graph
food_graph = create_food_suggestion_graph()
