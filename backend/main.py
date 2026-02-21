import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.apis.food.routes import router as food_router
from app.core.logger import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Smart Food Suggestion API",
    description="Multi-agent RAG system for personalized food recommendations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development, restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(food_router, prefix="/api/v1/food", tags=["Food Suggestions"])

@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "Smart Food Suggestion API"}

if __name__ == "__main__":
    logger.info("🚀 Starting FastAPI Server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
