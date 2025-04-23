from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
)

# Load OpenAI key (create a .env file with OPENAI_KEY="your-api-key")
openai.api_key = os.getenv("OPENAI_KEY")

class HealthReport(BaseModel):
    conditions: list
    recommendations: list
    emergency: bool

@app.get("/analyze")
async def analyze_health(question: str):
    """Uses LLM to analyze health queries"""
    prompt = f"""
    As a medical assistant, analyze this symptom: '{question}'. 
    Return JSON with:
    1. "conditions": [top 3 possible conditions],
    2. "recommendations": [personalized advice],
    3. "emergency": boolean (true if needs urgent care)
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3  # Lower = more deterministic
    )
    
    return eval(response.choices[0].message.content)  # Converts JSON string to dict