# Quick Start Guide

## 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## 2. Start the Server

```bash
# Option 1: Using the run script
python run.py

# Option 2: Using uvicorn directly
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 3. Open the Frontend

### Option A: Direct File Open
Simply open `frontend/index.html` in your web browser.

**Note**: For CORS to work properly, you may need to serve the frontend through a web server:

```bash
cd frontend
python -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

### Option B: Serve with Backend (Recommended)
The frontend can be served by the FastAPI backend (requires additional setup).

## 4. Configure LLM Provider (Optional)

By default, the system uses Hugging Face Inference API. Some models work without an API key.

### Hugging Face (Default)
```bash
export HUGGINGFACE_API_KEY="your-key-here"  # Optional for some models
```

### OpenRouter (Free tier available)
```bash
export OPENROUTER_API_KEY="your-key-here"
export LLM_PROVIDER="openrouter"
```

### Ollama (Local)
```bash
# Install Ollama first: https://ollama.ai
export LLM_PROVIDER="ollama"
```

## 5. Test the System

### Using the Web Interface

1. Open the frontend in your browser
2. Paste text or upload a file
3. Click "Analyze Document"
4. Watch the real-time progress (if enabled)
5. View the final report

### Using the API Directly

```bash
# Text analysis
curl -X POST "http://localhost:8000/api/analyze/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your document text here", "show_updates": false}'

# File upload
curl -X POST "http://localhost:8000/api/analyze/file" \
  -F "file=@your-document.pdf" \
  -F "show_updates=false"
```

### Using Python

```bash
python example_usage.py
```

## 6. View History

Access analysis history via:
- Web UI: History section at the bottom
- API: `GET http://localhost:8000/api/history`

## Troubleshooting

### CORS Errors
If you see CORS errors, make sure:
- The frontend is being served (not just opened as a file)
- The API is running on the expected port
- CORS is enabled in the backend (it is by default)

### LLM Errors
- Check your API keys are set correctly
- For Hugging Face, some models may be slow or unavailable
- Try a different provider if one doesn't work

### File Upload Issues
- Ensure file is not too large
- Check file format is supported (TXT, MD, PDF, DOCX)
- For PDF/DOCX, ensure PyPDF2 and python-docx are installed

### Port Already in Use
Change the port:
```bash
export PORT=8001
python run.py
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the agent architecture in the `agents/` directory
- Customize the LLM prompts in each agent file
- Modify the coordination layer in `coordination/message_bus.py`

