from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from urllib.parse import parse_qs, quote
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv

import auth
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

def get_base_url(request: Request) -> str:
    """
    Get the correct base URL respecting X-Forwarded-Proto header from reverse proxy.
    This is critical when running behind nginx with SSL termination.
    """
    # Check X-Forwarded-Proto header (set by nginx/reverse proxy)
    forwarded_proto = request.headers.get("x-forwarded-proto", None)
    forwarded_host = request.headers.get("x-forwarded-host", None)
    host = request.headers.get("host", str(request.base_url.netloc))
    
    # Debug logging
    logger.info(f"Headers: X-Forwarded-Proto={forwarded_proto}, X-Forwarded-Host={forwarded_host}, Host={host}")
    
    if forwarded_proto:
        # We're behind a reverse proxy with proper headers
        actual_host = forwarded_host or host
        return f"{forwarded_proto}://{actual_host}"
    
    # Fallback: If host is a real domain (not localhost), assume HTTPS
    # This handles cases where reverse proxy doesn't send X-Forwarded-Proto
    if host and not host.startswith("localhost") and not host.startswith("127.") and ":" not in host.split(".")[0]:
        # Looks like a domain name (e.g., vocas.mirecek.org) - use HTTPS
        return f"https://{host}"
    
    # Local development - use base_url as-is
    return str(request.base_url).rstrip('/')

if not auth.auth_enabled():
    logger.warning("USR/PAS not set - authentication is DISABLED")


@app.middleware("http")
async def require_login(request: Request, call_next):
    """Gate everything except the login page behind the session cookie."""
    path = request.url.path
    if (
        not auth.auth_enabled()
        or path in auth.PUBLIC_PATHS
        or auth.valid_token(request.cookies.get(auth.COOKIE_NAME))
    ):
        return await call_next(request)
    if path.startswith("/api/"):
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    target = request.url.path + (f"?{request.url.query}" if request.url.query else "")
    return RedirectResponse(f"/login?next={quote(target)}", status_code=303)


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Services
proxy_service = ProxyService()
llm_service = LLMService(
    api_key=os.getenv("GEMINI_API_KEY"),
    model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
)

# TTS Service - provider from ENV (default: edge)
tts_provider = os.getenv("TTS_PROVIDER", "edge")
tts_service = TTSService(output_dir="static/audio", provider=tts_provider)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/"):
    return templates.TemplateResponse(
        request, "login.html", {"next": auth.safe_next(next), "error": False}
    )


@app.post("/login")
async def login(request: Request):
    # Parse urlencoded form by hand to avoid the python-multipart dependency
    form = parse_qs((await request.body()).decode(), keep_blank_values=True)
    username = form.get("username", [""])[0]
    password = form.get("password", [""])[0]
    next_url = auth.safe_next(form.get("next", ["/"])[0])

    if not auth.auth_enabled() or not auth.check_credentials(username, password):
        logger.warning("Failed login attempt for user %r", username)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"next": next_url, "error": True},
            status_code=401,
        )

    response = RedirectResponse(next_url, status_code=303)
    response.set_cookie(
        auth.COOKIE_NAME,
        auth.make_token(),
        max_age=auth.COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=get_base_url(request).startswith("https://"),
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(auth.COOKIE_NAME)
    return response


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
    return templates.TemplateResponse(request, "index.html")

@app.get("/read/{url:path}", response_class=HTMLResponse)
async def read_url(request: Request, url: str):
    """
    Proxy endpoint. Fetches URL and injects overlay.
    """
    # Base host for injecting scripts - respects X-Forwarded-Proto from nginx
    base_host = get_base_url(request)
    
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
