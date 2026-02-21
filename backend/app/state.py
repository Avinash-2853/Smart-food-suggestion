from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    Shared state across all nodes in the LangGraph food suggestion workflow.
    """
    user_query: str                  # Original input query
    user_profile: Dict[str, Any]     # Extracted constraints (budget, diet, tags)
    current_suggestions: List[Dict[str, Any]] # Raw data results from SQL/Vector search
    menu_draft: str                  # The generated menu text
    critic_feedback: Optional[str]   # Feedback if manual revision is needed
    nutrition_summary: Dict[str, Any] # Combined nutritional stats (cals, protein)
    final_output: str                # Final message to be displayed to the user
    structured_output: Optional[Dict[str, Any]] # Final structured response for API
    iteration_count: int             # To prevent infinite looping (max 3)
    approved: bool                   # Fast-exit flag for the graph router
    error_reason: Optional[str]      # Reason for rejection in validation phase
    revision_instructions: Optional[Dict[str, Any]] # Specific instructions for the searcher
    selected_restaurants: List[str]  # IDs of restaurants involved in the draft
    total_cost: float                # Sum of menu prices
