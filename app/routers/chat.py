"""Chat router for AI assistant interactions."""

import uuid
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import get_settings
from app.services.rag_engine import RAGEngine

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()
templates = Jinja2Templates(directory=str(settings.templates_dir))

# In-memory session storage (for demo purposes)
chat_sessions: dict[str, list[dict]] = {}


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request, session_id: str = None):
    """Render the chat interface."""
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
    
    # Get conversation history for this session
    messages = chat_sessions.get(session_id, [])
    
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "session_id": session_id,
            "messages": messages,
            "title": "Chat - UVA Course Assistant",
        }
    )


@router.post("/send", response_class=HTMLResponse)
async def send_message(
    request: Request,
    message: str = Form(...),
    session_id: str = Form(...),
):
    """Process a chat message and return response."""
    # Initialize session if needed
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    
    # Add user message
    chat_sessions[session_id].append({
        "role": "user",
        "content": message,
    })
    
    try:
        # Get RAG response
        rag_engine = RAGEngine()
        result = rag_engine.query(message)
        
        response_text = result["response"]
        sources = result.get("sources", [])
        
        # Format sources if any
        if sources:
            source_text = "\n\n📚 Sources: " + ", ".join(sources[:3])
            response_text += source_text
        
    except Exception as e:
        response_text = f"I apologize, but I encountered an error processing your request. Please try again. (Error: {str(e)})"
    
    # Add assistant response
    chat_sessions[session_id].append({
        "role": "assistant",
        "content": response_text,
    })
    
    # Redirect back to chat page
    return RedirectResponse(
        url=f"/chat?session_id={session_id}",
        status_code=303,
    )


@router.post("/clear", response_class=HTMLResponse)
async def clear_chat(session_id: str = Form(...)):
    """Clear chat history for a session."""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    
    return RedirectResponse(
        url=f"/chat?session_id={session_id}",
        status_code=303,
    )

