# Project AETHER - Multi-Agent Deliberative Reasoning System

Project AETHER is an advanced multi-agent AI system that analyzes complex reports, case studies, or documents through structured debates between specialized AI agents.

## Features

- **Multi-Agent Architecture**: Five specialized agents working in coordination
- **Structured Debates**: Each factor is debated with supporting arguments, critiques, and rebuttals
- **Transparent Reasoning**: Exposes debate highlights and key disagreements
- **Multiple Input Methods**: Text paste or file upload (TXT, MD, PDF, DOCX)
- **Real-time Updates**: Optional toggle to view/hide analysis progress
- **Analysis History**: Saves key points from previous analyses
- **Free LLM Support**: Works with Hugging Face, OpenRouter, and Ollama
- **File Format Support**: Automatic parsing of PDF and DOCX files (requires PyPDF2 and python-docx)

## Architecture

### Agents

1. **Factor Extraction Agent**: Identifies key factors from input
2. **Supporting Agent**: Argues in favor of each factor
3. **Critic Agent**: Challenges each factor with critiques
4. **Synthesizer Agent**: Extracts insights from all debates
5. **Final Decision Agent**: Generates unified final report

### Coordination Layer

All agents communicate through a message bus with structured message types:
- `FACTOR_LIST`
- `SUPPORT_ARGUMENT`
- `CRITIQUE`
- `REBUTTAL`
- `SYNTHESIS_NOTE`
- `FINAL_DIRECTIVE`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd HackSync
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: For PDF and DOCX support, the required libraries (PyPDF2 and python-docx) are included in requirements.txt. If you only need text file support, you can skip these.

3. Set up LLM provider (optional):
```bash
# For Hugging Face (default, works without API key for some models)
export HUGGINGFACE_API_KEY="your-key-here"

# For OpenRouter
export OPENROUTER_API_KEY="your-key-here"
export LLM_PROVIDER="openrouter"

# For Ollama (local)
export LLM_PROVIDER="ollama"
```

## Usage

### Start the Backend

```bash
python -m api.main
```

Or using uvicorn directly:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Frontend

Open `frontend/index.html` in a web browser, or serve it with a simple HTTP server:

```bash
cd frontend
python -m http.server 8080
```

Then navigate to `http://localhost:8080`

### API Endpoints

- `POST /api/analyze/text` - Analyze text input
- `POST /api/analyze/file` - Analyze uploaded file
- `GET /api/analyze/stream/{session_id}` - Stream analysis updates (SSE)
- `GET /api/history` - Get analysis history
- `GET /api/history/{analysis_id}` - Get specific analysis

## Workflow

1. **Factor Extraction**: Agent identifies all key factors
2. **For Each Factor**:
   - Supporting Agent generates arguments
   - Critic Agent challenges the arguments
   - Supporting Agent may rebut once
3. **Synthesis**: Synthesizer Agent reviews all debates
4. **Final Report**: Final Decision Agent generates structured report

## Output Format

The final report follows this structure:

```
=== PROJECT AETHER FINAL REPORT ===

1. Problem Overview
2. Key Factors Identified
3. Debate Summary (Pros vs Cons)
4. Root Cause Analysis
5. What Worked
6. What Failed
7. Why It Happened
8. Actionable Recommendations
9. Risks & Limitations
10. Final Verdict

==================================
```

## LLM Providers

### Hugging Face (Default)
- Works with free models
- Some models don't require API key
- Set `HUGGINGFACE_API_KEY` for better models

### OpenRouter
- Access to multiple free and paid models
- Requires API key
- Set `OPENROUTER_API_KEY` and `LLM_PROVIDER=openrouter`

### Ollama
- Run models locally
- No API key needed
- Set `LLM_PROVIDER=ollama`
- Requires Ollama installed locally

## History Storage

Analysis history is stored in SQLite database (`aether_history.db`). Only key points are saved to minimize storage:
- Factor names
- Final verdict summary
- Top recommendations

## Development

### Project Structure

```
HackSync/
├── agents/              # Agent implementations
│   ├── base_agent.py
│   ├── factor_extraction_agent.py
│   ├── supporting_agent.py
│   ├── critic_agent.py
│   ├── synthesizer_agent.py
│   └── final_decision_agent.py
├── coordination/       # Message bus
│   └── message_bus.py
├── llm/                # LLM client interfaces
│   └── llm_client.py
├── workflow/           # Orchestration
│   └── orchestrator.py
├── storage/            # History storage
│   └── history.py
├── api/                # FastAPI backend
│   └── main.py
├── frontend/           # Web UI
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── requirements.txt
└── README.md
```

## License

MIT License

## Contributing

Contributions welcome! Please ensure:
- Agents remain independent (no shared state)
- All communication goes through message bus
- Execution order is strictly followed
- Reasoning transparency is maintained

