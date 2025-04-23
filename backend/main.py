from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
)

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # Uses your key from .env

class Conversation(BaseModel):
    user_input: str
    history: list = []

def query_deepseek(prompt: str) -> dict:
    """Send prompt to DeepSeek API and return parsed JSON"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,  # More deterministic medical responses
        "response_format": {"type": "json_object"}
    }

    try:
        print("Payload:", payload)  # Debugging
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        print("Response Status Code:", response.status_code)  # Debugging
        print("Response Content:", response.text)  # Debugging
        response.raise_for_status()
        return eval(response.json()["choices"][0]["message"]["content"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DeepSeek API error: {str(e)}")

@app.post("/analyze")
async def analyze_symptoms(conv: Conversation):
    prompt = f"""
    [Medical Assistant Task]
    Analyze this symptom: {conv.user_input}
    Conversation History: {conv.history}

    Return JSON with:
    - "analysis": "brief summary",
    - "questions": ["follow-up question 1", "question 2"],
    - "action": "monitor|urgent_care" 
    """
    
    return query_deepseek(prompt)