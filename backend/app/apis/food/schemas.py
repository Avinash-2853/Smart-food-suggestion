from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FoodItem(BaseModel):
    item_name: str = Field(..., alias="itemName")
    price: float = Field(..., alias="price")
    description: str = Field(..., alias="description")
    explanation: str = Field(..., alias="explanation")
    restaurant_name: Optional[str] = Field(None, alias="restaurantName")
    protein_g: Optional[float] = Field(None, alias="proteinG")
    calories: Optional[int] = Field(None, alias="calories")

    class Config:
        populate_by_name = True

class SuggestionRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    location: Optional[str] = None

class SuggestionResponse(BaseModel):
    suggestions: List[FoodItem]
    summary: str
    metadata: Dict[str, Any] = {}
