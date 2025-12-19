"""Chat/Agent conversation endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.agent.orchestrator import BakeryQuotationAgent
from src.config import Config
from src.app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

# Store active sessions (in production, use Redis or similar)
active_sessions: dict[str, BakeryQuotationAgent] = {}


class ChatMessage(BaseModel):
    """Chat message from user."""

    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., min_length=1, description="User message")
    session_id: str = Field(..., description="Session identifier")
    history: list[ChatMessage] = Field(default_factory=list, description="Chat history")


class ChatResponse(BaseModel):
    """Response from chat agent."""

    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session identifier")


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the bakery quotation agent.

    The agent will guide the user through creating a quotation via conversation.
    """
    try:
        logger.info(f"Chat request - Session: {request.session_id}, Message: {request.message[:50]}...")

        # Get or create agent for this session
        if request.session_id not in active_sessions:
            logger.info(f"Creating new agent session: {request.session_id}")
            config = Config.from_env()
            active_sessions[request.session_id] = BakeryQuotationAgent(config)

        agent = active_sessions[request.session_id]

        # Process the message through the agent
        result = agent.invoke(request.message)
        response = result.get("output", str(result))

        logger.info(f"Agent response length: {len(response)}")

        return ChatResponse(
            response=response,
            session_id=request.session_id
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {str(e)}"
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_session(session_id: str):
    """Clear a chat session."""
    if session_id in active_sessions:
        del active_sessions[session_id]
        logger.info(f"Cleared session: {session_id}")
    return None


@router.get("/sessions", response_model=list[str])
async def list_sessions() -> list[str]:
    """List active chat sessions."""
    return list(active_sessions.keys())
