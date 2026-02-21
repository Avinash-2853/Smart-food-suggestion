from fastapi import APIRouter, HTTPException
from app.apis.food.schemas import SuggestionRequest, SuggestionResponse, FoodItem
from app.graph import food_graph
from app.core.logger import logger
import uuid

router = APIRouter()

@router.post("/suggest", response_model=SuggestionResponse)
async def get_food_suggestions(payload: SuggestionRequest):
    """
    Endpoint to trigger the multi-agent food suggestion workflow.
    """
    logger.info(f"📥 Received suggestion request: {payload.query}")
    
    try:
        # Initialize state
        initial_state = {
            "user_query": payload.query,
            "user_profile": {"location": payload.location},
            "current_suggestions": [],
            "menu_draft": "",
            "critic_feedback": None,
            "nutrition_summary": {},
            "final_output": "",
            "structured_output": None,
            "iteration_count": 0,
            "approved": False,
            "selected_restaurants": [],
            "total_cost": 0.0
        }
        
        # Run the graph
        final_state = await food_graph.ainvoke(initial_state)
        
        # Extract structured output
        structured = final_state.get("structured_output")
        if not structured or "items" not in structured:
             # Fallback if AI didn't provide JSON
             return SuggestionResponse(
                 summary=final_state.get("final_output", "No summary available."),
                 suggestions=[],
                 metadata={"error": "Structured output missing"}
             )
        
        # Map items to Pydantic models
        food_items = []
        for item in structured.get("items", []):
            food_items.append(FoodItem(
                itemName=item.get("itemName", "Unknown Item"),
                price=item.get("price", 0.0),
                description=item.get("description", ""),
                explanation=item.get("explanation", ""),
                restaurantName=item.get("restaurantName", "Unknown Restaurant")
            ))
            
        return SuggestionResponse(
            summary=structured.get("summary", ""),
            suggestions=food_items,
            metadata={
                "total_cost": final_state.get("total_cost", 0.0),
                "party_size": final_state.get("user_profile", {}).get("party_size", 1)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error in suggestion API: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
