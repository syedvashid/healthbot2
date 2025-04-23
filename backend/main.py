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

# Initialize FastAPI
app = FastAPI()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    query: str
    language: str = "en"

class ChatResponse(BaseModel):
    reply: str

# Config
os.makedirs("reports", exist_ok=True)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Set your key in .env

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # LLM Call
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
        with open("reports/latest_chat.txt", "a") as f:
            f.write(f"{timestamp} | User: {request.query}\n")
            f.write(f"{timestamp} | Bot: {reply}\n\n")

        return {"reply": reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate-summary")
async def generate_summary():
    try:
        # Create PDF
        pdf_path = f"reports/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph("Health Chat Summary", styles["Title"])]

        with open("reports/latest_chat.txt", "r") as f:
            for line in f:
                story.append(Paragraph(line.strip(), styles["Normal"]))

        doc.build(story)
        return {"status": "PDF generated", "path": pdf_path}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No chats found")

@app.get("/download-pdf")
async def download_pdf():
    try:
        with open("reports/latest_summary.pdf", "rb") as f:
            return Response(
                content=f.read(),
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=health_summary.pdf"}
            )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="PDF not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)