from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import pytz
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import os
import openai
from typing import Optional

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all for debugging
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    query: str
    language: str = "en"

class ChatResponse(BaseModel):
    reply: str

# Configuration
os.makedirs("reports", exist_ok=True)
openai.api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")  # Fallback for testing

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not openai.api_key or openai.api_key == "your-api-key-here":
            raise ValueError("OpenAI API key not configured")
            
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a medical assistant. Respond in {request.language}."},
                {"role": "user", "content": request.query}
            ],
            temperature=0.7
        )
        reply = response.choices[0].message.content

        # Log chat
        timestamp = datetime.now(pytz.timezone("UTC")).strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} | {request.language} | User: {request.query}\nBot: {reply}\n\n"
        
        with open("reports/chat_log.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)

        return {"reply": reply}

    except Exception as e:
        error_msg = f"LLM Error: {str(e)}"
        print(error_msg)  # Debug print
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/generate-summary")
async def generate_summary():
    try:
        input_file = "reports/chat_log.txt"
        output_file = "reports/latest_summary.pdf"
        
        if not os.path.exists(input_file):
            raise HTTPException(status_code=404, detail="No chat history found")

        # Create PDF
        doc = SimpleDocTemplate(output_file, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph("Health Chat Summary", styles["Title"])]

        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                story.append(Paragraph(line.strip(), styles["Normal"]))

        doc.build(story)
        return {"status": "success", "path": output_file}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download-pdf")
async def download_pdf():
    pdf_path = "reports/latest_summary.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found. Generate it first.")
    
    with open(pdf_path, "rb") as f:
        return Response(
            content=f.read(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=health_summary.pdf"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)