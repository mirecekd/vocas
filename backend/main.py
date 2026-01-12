from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv

from services.proxy import ProxyService
from services.llm import LLMService
from services.tts import TTSService
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vocas 2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Services
proxy_service = ProxyService()
llm_service = LLMService(api_key=os.getenv("GEMINI_API_KEY"))

# TTS Service - provider from ENV (default: edge)
tts_provider = os.getenv("TTS_PROVIDER", "edge")
tts_service = TTSService(output_dir="static/audio", provider=tts_provider)

class ProcessRequest(BaseModel):
    text: str
    mode: str = "read" # 'read' or 'summarize'

@app.on_event("shutdown")
async def shutdown_event():
    await proxy_service.close()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Homepage with search bar and quick links.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/read/{url:path}", response_class=HTMLResponse)
async def read_url(request: Request, url: str):
    """
    Proxy endpoint. Fetches URL and injects overlay.
    """
    # Base host for injecting scripts (e.g., http://localhost:5000)
    base_host = str(request.base_url).rstrip('/')
    
    html_content = await proxy_service.fetch_and_process(url, base_host)
    
    # Return HTML. 
    # Important: We strip Content-Security-Policy to allow our injected scripts to run.
    response = HTMLResponse(content=html_content)
    if "content-security-policy" in response.headers:
        del response.headers["content-security-policy"]
    
    return response

@app.post("/api/process")
async def process_content(request: ProcessRequest):
    """
    Processes text (cleaning/reasoning/summarizing) and generates audio.
    """
    logger.info(f"Processing request: mode={request.mode}, text_len={len(request.text)}")
    
    processed_text = ""
    if request.mode == "summarize":
        processed_text = llm_service.summarize_text(request.text)
    else:
        # 'read' mode - clean logic
        processed_text = llm_service.clean_text(request.text)
    
    logger.info(f"LLM processed text length: {len(processed_text)}")
    
    audio_file = tts_service.generate_audio(processed_text)
    
    if not audio_file:
        raise HTTPException(status_code=500, detail="Failed to generate audio")
        
    return {
        "audio_url": f"/static/audio/{audio_file}",
        "processed_text": processed_text
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
