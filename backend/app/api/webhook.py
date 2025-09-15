# backend/app/api/webhook.py
from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import BaseResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test")
async def webhook_test():
    """웹훅 테스트 엔드포인트"""
    return BaseResponse(
        message="웹훅 API 준비됨",
        success=True
    )

@router.post("/external")
async def handle_external_webhook(request: Request):
    """외부 서비스 웹훅 처리"""
    # TODO: 실제 웹훅 처리 로직 구현
    body = await request.json()
    logger.info(f"웹훅 수신: {body}")
    
    return BaseResponse(
        message="웹훅 처리 완료",
        success=True
    )

# TODO: 추가 웹훅들
# 예시:
# - 카카오톡 챗봇
# - 슬랙 봇
# - 디스코드 봇
# - 결제 시스템 콜백
# - 외부 API 콜백