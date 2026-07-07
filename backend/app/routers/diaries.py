from fastapi import APIRouter, Query

from ..schemas.diaries import DiaryListResponse, DiaryResponse
from ..services.diary_service import get_diary, list_diaries


router = APIRouter(prefix="/api/v1/diaries", tags=["diaries"])


@router.get("", response_model=DiaryListResponse)
def read_diaries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return {"diaries": list_diaries(page=page, page_size=page_size)}


@router.get("/{diary_id}", response_model=DiaryResponse)
def read_diary(diary_id: str):
    return get_diary(diary_id)
