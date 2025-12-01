from pydantic import BaseModel, Field
from typing import Optional

# --- 1. CORE NUTRITIONAL DATA SCHEMA (matches Gemini structured output) ---

class NutritionalSummary(BaseModel):
    """The detailed breakdown of macronutrients."""
    total_calories: int = Field(..., description="Estimated total calories for the portion.")
    protein_g: float = Field(..., description="Estimated grams of protein.")
    carbohydrates_g: float = Field(..., description="Estimated grams of carbohydrates.")
    fat_g: float = Field(..., description="Estimated grams of total fat.")

class NutritionResult(BaseModel):
    """The full structured output received from the Gemini analysis."""
    food_identification: str = Field(..., description="The specific name of the food item identified.")
    portion_estimate: str = Field(..., description="A textual estimation of the portion size.")
    nutritional_summary: NutritionalSummary
    disclaimer: str = Field(..., description="A brief safety disclaimer provided by the model.")

# --- 2. API REQUEST & RESPONSE SCHEMAS ---

class ScanResponse(BaseModel):
    """Schema for the successful response after a meal scan."""
    meal_id: str = Field(..., description="Unique identifier for the saved meal history record.")
    food_identification: str = Field(..., description="The primary food item recognized.")
    total_calories: float = Field(..., description="The total estimated calories.")
    message: str = Field(..., description="A confirmation message.")

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str = Field(..., description="Description of the error that occurred.")
    
# --- 3. DATABASE RECORD SCHEMAS (For fetching history from Supabase) ---

class MealHistoryRecord(BaseModel):
    """Schema for fetching saved records from the Supabase 'meal_history' table."""
    id: str
    user_id: str
    food_identification: str
    total_calories: int
    image_url: str = Field(..., description="Public URL where the image is stored.")
    # The JSON data is stored as a JSONB type in Postgres, retrieved as a Python dict/JSON
    nutrition_data_json: NutritionResult
    created_at: str
    
    class Config:
        # Allows fields to be accessed like dictionary keys (e.g., record['id'])
        from_attributes = True