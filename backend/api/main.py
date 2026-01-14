"""
FastAPI Backend for Project AETHER
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
import sys
import os
import asyncio
import json
from sse_starlette.sse import EventSourceResponse
from enum import Enum

# Add parent directory to path to access storage module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from workflow.orchestrator import Orchestrator
from llm.llm_client import create_llm_client, LLMProvider
from storage.history import HistoryStorage
from utils.file_parser import parse_file_content

app = FastAPI(title="Project AETHER API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
llm_provider_name = os.getenv("LLM_PROVIDER", "huggingface").lower()
llm_client = None  # Lazy initialization
history_storage = HistoryStorage()

def get_llm_client():
    """Lazy initialization of LLM client."""
    global llm_client
    if llm_client is None:
        try:
            llm_client = create_llm_client(LLMProvider(llm_provider_name))
            print(f"✓ LLM Client initialized: {llm_provider_name}")
        except Exception as e:
            print(f"✗ Error initializing LLM client: {e}")
            # Fallback to HuggingFace
            llm_client = create_llm_client(LLMProvider.HUGGINGFACE)
            print("✓ Fallback to HuggingFace client")
    return llm_client

# Store active orchestrators (for SSE)
active_orchestrators = {}


def _serialize_message_types(obj: Any) -> Any:
    """Recursively convert MessageType enums to strings for JSON serialization."""
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {k: _serialize_message_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_message_types(item) for item in obj]
    else:
        return obj


class TextInput(BaseModel):
    text: str
    show_updates: bool = True


class AnalysisRequest(BaseModel):
    text: str
    show_updates: bool = True


@app.get("/")
async def root():
    return {"message": "Project AETHER API", "status": "running"}


@app.post("/api/analyze/text")
async def analyze_text(request: AnalysisRequest):
    """Analyze text input."""
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text input cannot be empty")
        
        orchestrator = Orchestrator(get_llm_client())
        
        result = await orchestrator.analyze(request.text, request.show_updates)
        
        # Ensure result is a dict
        if not isinstance(result, dict):
            result = {"success": False, "error": "Invalid result format from orchestrator"}
        
        # Ensure all MessageType enums are converted to strings for JSON serialization
        result = _serialize_message_types(result)
        
        # Save to history
        if result.get("success"):
            try:
                analysis_id = history_storage.save_analysis(result)
                result["analysis_id"] = analysis_id
            except Exception as e:
                print(f"Warning: Failed to save to history: {e}")
                # Don't fail the request if history save fails
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error in analyze_text: {error_msg}")
        print(error_trace)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {error_msg}")


@app.post("/api/analyze/file")
async def analyze_file(file: UploadFile = File(...), show_updates: bool = True):
    """Analyze uploaded file."""
    try:
        # Read file content
        content = await file.read()
        filename = file.filename or "unknown"
        
        # Parse file based on type
        try:
            text = parse_file_content(content, filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="File is empty or contains no text")
        
        orchestrator = Orchestrator(get_llm_client())
        result = await orchestrator.analyze(text, show_updates)
        
        # Ensure all MessageType enums are converted to strings for JSON serialization
        result = _serialize_message_types(result)
        
        # Save to history
        if result.get("success"):
            try:
                analysis_id = history_storage.save_analysis(result)
                result["analysis_id"] = analysis_id
            except Exception as e:
                print(f"Warning: Failed to save to history: {e}")
                # Don't fail the request if history save fails
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error in analyze_file: {error_msg}")
        print(error_trace)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {error_msg}")


@app.get("/api/analyze/stream/{session_id}")
async def analyze_stream(session_id: str, text: str, show_updates: bool = True):
    """Stream analysis updates via SSE."""
    
    async def event_generator():
        # Send initial connection confirmation immediately
        try:
            yield {
                "event": "message",
                "data": json.dumps({
                    "event": "connected",
                    "data": {"message": "Connection established, starting analysis..."}
                })
            }
        except Exception as e:
            print(f"Error sending initial message: {e}")
            return
        
        try:
            # Initialize orchestrator
            try:
                orchestrator = Orchestrator(get_llm_client())
            except Exception as e:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "event": "error",
                        "data": {"error": f"Failed to initialize orchestrator: {str(e)}"}
                    })
                }
                return
            
            # Store orchestrator for this session
            active_orchestrators[session_id] = orchestrator
            
            # Set up progress callback with queue
            progress_queue = asyncio.Queue()
            
            def progress_callback(update):
                try:
                    progress_queue.put_nowait(update)
                except:
                    pass  # Queue full, skip update
            
            orchestrator.set_progress_callback(progress_callback)
            
            # Start analysis in background
            try:
                analysis_task = asyncio.create_task(orchestrator.analyze(text, show_updates))
            except Exception as e:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "event": "error",
                        "data": {"error": f"Failed to start analysis: {str(e)}"}
                    })
                }
                return
            
            # Stream progress updates
            while True:
                try:
                    # Check if analysis is done
                    if analysis_task.done():
                        result = await analysis_task
                        
                        # Save to history
                        if result.get("success"):
                            analysis_id = history_storage.save_analysis(result)
                            result["analysis_id"] = analysis_id
                        
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "event": "complete",
                                "data": result
                            })
                        }
                        
                        # Clean up
                        if session_id in active_orchestrators:
                            del active_orchestrators[session_id]
                        
                        return
                    
                    # Try to get progress update (non-blocking)
                    try:
                        update = progress_queue.get_nowait()
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "event": "progress",
                                "data": update
                            })
                        }
                    except asyncio.QueueEmpty:
                        # No update yet, wait a bit
                        await asyncio.sleep(0.1)
                
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "event": "error",
                            "data": {"error": str(e)}
                        })
                    }
                    break
        
        except Exception as e:
            import traceback
            error_details = str(e)
            print(f"SSE Error: {error_details}")
            print(traceback.format_exc())
            yield {
                "event": "message",
                "data": json.dumps({
                    "event": "error",
                    "data": {"error": error_details}
                })
            }
    
    return EventSourceResponse(event_generator())


@app.get("/api/history")
async def get_history(limit: int = 50):
    """Get analysis history."""
    try:
        history = history_storage.get_history(limit)
        return JSONResponse(content={"history": history})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/{analysis_id}")
async def get_analysis(analysis_id: int):
    """Get specific analysis by ID."""
    try:
        analysis = history_storage.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return JSONResponse(content=analysis)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

