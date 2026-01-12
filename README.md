# VOCAS 2.0

Voice Oriented Content Aggregation System - A universal web reading proxy with AI-powered content processing and text-to-speech.

<div align="center">

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mirecekdg)

</div>

## What is VOCAS?

VOCAS 2.0 is a web application that works as a "reading proxy". It allows you to load any web page and adds voice reading controls with AI summarization overlay.

## How it works?

### 1. Enter URL
- Type any web address or click a quick bookmark
- The page loads through VOCAS proxy with an overlay control panel

### 2. AI Processing
- Click "Read" to read the article (AI removes clutter like dates, weather, ads)
- Click "Summarize" to read a brief summary

### 3. Voice Reading
- Processed text is read using high-quality TTS (Edge TTS, ElevenLabs, or AWS Polly)
- Large buttons and dark mode for car-friendly usage

## Features

- **Full Proxy Mode**: All links stay within the proxy - browse the entire web with overlay
- **Quick Bookmarks**: Popular Czech news sites with real icons (Aktualne.cz, CT24, iRozhlas, HN.cz, Denik.cz, Lupa.cz, Root.cz, ScienceWorld.cz, 21stoleti.cz)
- **AI Content Cleaning**: Reads only relevant content using Google Gemini
- **AI Summarization**: Creates brief article summaries
- **Multi-TTS Support**: Three TTS providers - Edge (free), ElevenLabs, AWS Polly
- **Car-Friendly UI**: Large buttons and dark mode for safe usage while driving

## TTS Providers

VOCAS 2.0 supports 3 TTS providers. Selection is done in `.env` file using `TTS_PROVIDER`:

### Edge TTS (default, free)
```env
TTS_PROVIDER=edge
EDGE_VOICE=cs-CZ-AntoninNeural  # or cs-CZ-VlastaNeural
EDGE_RATE=+0%
EDGE_PITCH=+0Hz
```

**Advantages:** Free, good Czech voices, no API key needed.

### ElevenLabs (paid, best quality)
```env
TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=your_api_key
ELEVENLABS_VOICE_ID=your_voice_id
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

**Advantages:** Excellent quality, natural voices, many languages.

### AWS Polly (paid, Czech voice Iveta)
```env
TTS_PROVIDER=polly
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=eu-central-1
POLLY_VOICE_ID=Iveta
```

**Advantages:** Reliable, Czech neural voice Iveta.

## Technology Stack

### Backend
- Python 3.12
- FastAPI (async web framework)
- httpx (HTTP proxy)
- Google Gemini API (content processing and summarization)
- Edge TTS / ElevenLabs / AWS Polly (text-to-speech)
- BeautifulSoup4 (HTML parsing)

### Frontend
- Vanilla JavaScript
- CSS3 (dark mode, responsive design)
- Mozilla Readability (content extraction)

## Installation and Running

### Prerequisites

- Docker and Docker Compose
- API key for Google Gemini (free at https://aistudio.google.com/app/apikey)

### Docker Compose (Recommended)

```bash
# 1. Navigate to project folder
cd vocas

# 2. Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Start with Docker Compose
docker-compose up -d --build

# 4. Open in browser
http://localhost:5000
```

**Management commands:**
```bash
# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart

# Rebuild after changes
docker-compose up -d --build
```

### Docker (without docker-compose)

```bash
# 1. Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 2. Build and run
docker build -t vocas .

# Linux/Mac:
docker run -d \
  --name vocas \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/backend/static/audio:/app/static/audio \
  vocas

# Windows (PowerShell):
docker run -d `
  --name vocas `
  -p 5000:5000 `
  --env-file .env `
  -v ${PWD}/backend/static/audio:/app/static/audio `
  vocas

# 3. Application runs on http://localhost:5000
```

## Configuration

### Environment Variables (.env)

Create a `.env` file in the project root:

```env
# LLM (Gemini)
GEMINI_API_KEY=your_gemini_api_key_here

# TTS Provider Selection
# Options: edge, elevenlabs, polly
TTS_PROVIDER=edge

# Edge TTS (free, good Czech voices)
EDGE_VOICE=cs-CZ-AntoninNeural
EDGE_RATE=+0%
EDGE_PITCH=+0Hz

# ElevenLabs TTS (paid, excellent quality)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
ELEVENLABS_MODEL_ID=eleven_multilingual_v2

# AWS Polly TTS (paid, Czech voice Iveta)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=eu-central-1
POLLY_VOICE_ID=Iveta
```

Get Gemini API key at: https://aistudio.google.com/app/apikey

## Usage

1. On the homepage, enter article URL (e.g., `www.ihned.cz`) or click a quick bookmark
2. Page loads with floating control panel at the bottom
3. Click **Read** to read the article (AI removes clutter)
4. Click **Summarize** to read a brief summary
5. Click **Home** to return to homepage
6. Click **Stop** to stop playback

All links on the page are rewritten to stay within the proxy, allowing seamless navigation with the overlay.

## Project Structure

```
vocas/
├── backend/
│   ├── main.py                     # FastAPI application
│   ├── services/
│   │   ├── proxy.py               # HTTP proxy with link rewriting
│   │   ├── llm.py                 # Gemini LLM service
│   │   └── tts/                   # TTS providers
│   │       ├── __init__.py        # TTSService
│   │       ├── base.py            # Abstract TTS class
│   │       ├── edge_tts_provider.py      # Edge TTS
│   │       ├── elevenlabs_tts_provider.py # ElevenLabs
│   │       └── polly_tts_provider.py     # AWS Polly
│   ├── templates/
│   │   └── index.html             # Homepage
│   └── static/
│       ├── vocas-overlay.css      # Overlay styling
│       ├── vocas-overlay.js       # Overlay logic
│       └── audio/                 # Generated audio files
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## API Endpoints

- `GET /` - Homepage with search and bookmarks
- `GET /read/{url:path}` - Proxy endpoint (fetches URL and injects overlay)
- `POST /api/process` - Process text (clean/summarize) and generate audio

## Troubleshooting

### Missing API Key
```bash
# Make sure you have .env file with GEMINI_API_KEY
cp .env.example .env
# Edit .env and add your API key
```

### TTS Provider Issues
- **Edge TTS**: No API key needed, works out of the box
- **ElevenLabs**: Requires ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID
- **Polly**: Requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

Check logs for TTS initialization:
```bash
docker-compose logs | grep "TTS Service initialized"
```

### Port 5000 Already in Use
```bash
# Change port in docker-compose.yml from "5000:5000" to "8080:5000"
# Then app runs on http://localhost:8080
```

## Development

### Local Development (without Docker)

```bash
# 1. Create virtual environment
python -m venv venv

# Activate
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Run server
cd backend
python main.py

# 5. Open http://localhost:5000
```

## License

MIT License - see LICENSE file for details

## Author

Miroslav Dvorak - mirecekd@gmail.com

## Support

If you find this project useful, consider supporting its development:

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mirecekdg)
