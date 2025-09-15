# backend/app/api/admin.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import BaseResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def admin_status():
    """관리자 페이지 상태 확인"""
    return BaseResponse(
        message="관리자 API 준비됨",
        success=True
    )

# TODO: 관리자 기능들 추가 예정
# 예시:
# - 사용자 관리
# - 시스템 모니터링  
# - 데이터 관리
# - 설정 관리