from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_conversation_store, get_optional_user
from app.models.auth import UserProfile
from app.services.conversation import ConversationStore

router = APIRouter()


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: float
    updated_at: float
    message_count: int


class MessageItem(BaseModel):
    id: int
    role: str
    content: str
    metadata: dict | None = None
    created_at: float


class ConversationDetail(BaseModel):
    id: str
    user_id: str | None = None
    title: str
    created_at: float
    updated_at: float
    messages: list[MessageItem]


@router.get(
    "",
    response_model=list[ConversationSummary],
    summary="List chat sessions and history",
)
def list_conversations(
    store: ConversationStore = Depends(get_conversation_store),
    current_user: UserProfile | None = Depends(get_optional_user),
) -> list[ConversationSummary]:
    user_id = current_user.id if current_user else None
    return store.list_conversations(user_id=user_id)


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get full message history for a specific conversation",
)
def get_conversation(
    conversation_id: str,
    store: ConversationStore = Depends(get_conversation_store),
) -> ConversationDetail:
    history = store.get_conversation_history(conversation_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return ConversationDetail(**history)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a conversation session",
)
def delete_conversation(
    conversation_id: str,
    store: ConversationStore = Depends(get_conversation_store),
    current_user: UserProfile | None = Depends(get_optional_user),
) -> dict:
    user_id = current_user.id if current_user else None
    success = store.delete_conversation(conversation_id, user_id=user_id)
    return {"success": success, "conversation_id": conversation_id}


@router.post(
    "/clear",
    status_code=status.HTTP_200_OK,
    summary="Clear all conversations",
)
def clear_conversations(
    store: ConversationStore = Depends(get_conversation_store),
    current_user: UserProfile | None = Depends(get_optional_user),
) -> dict:
    user_id = current_user.id if current_user else None
    store.clear_all(user_id=user_id)
    return {"success": True, "message": "All chat history cleared."}
