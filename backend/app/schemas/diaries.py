from pydantic import BaseModel


class DiaryResponse(BaseModel):
    id: str
    conversation_id: str
    title: str
    content: str
    mood: str
    summary: str
    created_at: str
    updated_at: str


class DiaryListResponse(BaseModel):
    diaries: list[DiaryResponse]
