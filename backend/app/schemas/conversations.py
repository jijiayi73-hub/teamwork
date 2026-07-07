from pydantic import BaseModel, Field


class ConversationCreateResponse(BaseModel):
    conversation_id: str
    status: str
    created_at: str


class MessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str


class ConversationMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    status: str
    created_at: str
    updated_at: str
    messages: list[MessageResponse]
