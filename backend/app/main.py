import os
import json
import uuid
import traceback
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client, Client

# --- YOUR KEYS (Keep these) ---
GEMINI_API_KEY = "AIzaSyDAbbHg3G4PSSTDAO04GX0adkEWFXOZbw4"
SUPABASE_URL = "https://jkeaigdwaksqvcrtwctn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImprZWFpZ2R3YWtzcXZjcnR3Y3RuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUzNzUwMjEsImV4cCI6MjA4MDk1MTAyMX0.i8RhM9uikcWKUGHLacIyvhjjJyGTo62PXUKVSrW3loE"

# Initialize AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Database (Safe Mode)
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase Connected")
except Exception as e:
    print(f"⚠️ Supabase Init Failed (App will still work): {e}")
    supabase = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Kcalify AI Brain is Active 🧠"}

@app.post("/predict/calories")
async def predict_calories(
    file: UploadFile = File(...), 
    user_id: str = Query("guest_user", description="User ID for logging")
):
    print(f"🚀 Processing Request for: {file.filename}")
    
    try:
        # 1. Read Image
        image_bytes = await file.read()
        print("✅ Image Read")

        # 2. Ask AI
        prompt = """
        Analyze this food image. Identify the dish and estimate nutritional content.
        Return ONLY valid JSON. Do not write 'Here is the json'. Just the JSON.
        Format:
        {
            "food_name": "Dish Name",
            "calories": 0,
            "carbs": "0g",
            "protein": "0g",
            "fat": "0g",
            "confidence": 0.9
        }
        """
        
        try:
            response = model.generate_content([
                {'mime_type': file.content_type, 'data': image_bytes},
                prompt
            ])
            print("✅ AI Responded")
        except Exception as ai_error:
            # If AI fails (e.g., bad key), return mock data instead of crashing
            print(f"❌ AI Error: {ai_error}")
            return {
                "food_name": f"AI Error: {str(ai_error)[:20]}...",
                "calories": 0,
                "protein": "0g", "carbs": "0g", "fat": "0g", "confidence": 0.0
            }

        # 3. Safe Parse JSON
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        
        # FIX: Sometimes AI adds extra text. We try to find the first '{' and last '}'
        try:
            start_index = raw_text.find('{')
            end_index = raw_text.rfind('}') + 1
            if start_index != -1 and end_index != -1:
                clean_json = raw_text[start_index:end_index]
                food_data = json.loads(clean_json)
            else:
                raise ValueError("No JSON brackets found")
        except Exception as json_error:
            print(f"❌ JSON Parse Error. Raw text was: {raw_text}")
            return {
                "food_name": "Error: AI response invalid",
                "calories": 0,
                "protein": "0g", "carbs": "0g", "fat": "0g", "confidence": 0.0
            }

        # 4. Safe Database Save (This is usually where it crashes 500)
        if supabase:
            try:
                # We skip the insert if it looks like a test user to prevent crashes
                if "test_user" in user_id or "guest" in user_id:
                    print("⚠️ Skipping DB save for guest/test user to prevent UUID error")
                else:
                    log_entry = {
                        "user_id": user_id, 
                        "food_name": food_data.get('food_name', 'Unknown'),
                        "calories": int(food_data.get('calories', 0)),
                    }
                    supabase.table("food_logs").insert(log_entry).execute()
                    print("✅ Logged to Supabase")
            except Exception as db_error:
                print(f"⚠️ Database Error (Ignored): {db_error}")
                # We do NOT raise an error here. We just print it.

        return food_data

    except Exception as e:
        # Catch ALL other errors and return them to the phone screen
        error_msg = traceback.format_exc()
        print(f"❌ CRITICAL SERVER ERROR: {error_msg}")
        return {
            "food_name": f"Server Error: {str(e)}",
            "calories": 0,
            "protein": "0g", "carbs": "0g", "fat": "0g", "confidence": 0.0
        }