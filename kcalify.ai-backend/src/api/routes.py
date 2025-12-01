from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from typing import Optional

# Import models for input/output validation
from src.api.models import ScanResponse, ErrorResponse

# Import the core service layer
from src.core.meal_service import meal_service

router = APIRouter(
    prefix="/api/v1",
    tags=["nutrition"],
)
    
# -----------------------------------------------
# CORE ENDPOINT: /scan-meal
# -----------------------------------------------

@router.post(
    "/scan-meal/{user_id}", 
    response_model=ScanResponse, 
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    status_code=status.HTTP_201_CREATED
)
async def scan_meal(
    user_id: str,
    image_file: UploadFile = File(...),
):
    """
    Analyzes an uploaded food image using the Gemini API, stores the image 
    in cloud storage, and saves the nutritional result to Supabase.
    """
    
    # 1. Basic validation
    if not image_file.content_type.startswith('image/'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format. Must be an image.")

    # 2. Read the file bytes asynchronously
    image_bytes = await image_file.read()
    
    if len(image_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    try:
        # 3. Call the core service to handle all business logic (AI, DB, Storage)
        response = meal_service.process_and_save_meal(user_id, image_file, image_bytes)
        return response

    except ValueError as e:
        # Handles errors from Gemini analysis (e.g., Pydantic validation failure)
        print(f"Gemini/Validation Error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Analysis failed: {e}"
        )
    except Exception as e:
        # General catch-all for storage/DB/unhandled errors
        print(f"Critical processing failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="A critical server error occurred during processing. Please check logs."
        )