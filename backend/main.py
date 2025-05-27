from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional
import shutil
import os
from datetime import datetime
from chatbot.text_handler import TextMessageHandler
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()

app = FastAPI()
text_handler = TextMessageHandler()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Configure CORS with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],  # Vite dev server default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    text: str
    sessionId: str


class Message:
    def __init__(self, text: str, image_url: Optional[str] = None):
        self.text = text
        self.image_url = image_url
        self.timestamp = datetime.now().isoformat()


@app.post("/api/chat/text")
async def chat_text(message: dict):
    """
    Text chat endpoint using the text handler
    """
    if not message.get("text"):
        raise HTTPException(status_code=400, detail="Message text is required")

    response = await text_handler.handle_message(message["text"])
    return response


@app.post("/api/chat/text/v2")
async def chat_text_v2(message: ChatRequest):
    """
    Enhanced text chat endpoint using the new handler
    """
    if not message.text:
        raise HTTPException(status_code=400, detail="Message text is required")
    if not message.sessionId:
        raise HTTPException(status_code=400, detail="Session ID is required")

    response = await text_handler.handle_message(message.text, message.sessionId)
    return response


@app.post("/api/chat/image")
async def chat_image(
    image: UploadFile = File(...),
    sessionId: str = Form(...),  # Use Form to get the sessionId from form data
):
    """
    Image chat endpoint that handles multipart form data with image and sessionId
    """
    if not sessionId:
        raise HTTPException(status_code=400, detail="Session ID is required")

    # Save the uploaded image
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(image.filename)[1]
    filename = f"image_{timestamp}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # Generate image URL
    image_url = f"/api/images/{filename}"

    # Get image analysis
    response = await text_handler.handle_image_search(file_path, image_url, sessionId)

    # Add timestamp to response
    response["timestamp"] = datetime.now().isoformat()

    return response


@app.get("/api/images/{image_name}")
async def get_image(image_name: str):
    image_path = os.path.join(UPLOAD_DIR, image_name)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    raise HTTPException(status_code=404, detail="Image not found")
