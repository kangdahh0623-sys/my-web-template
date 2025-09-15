# backend/app/api/main.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import BaseResponse
import logging
from app.api import analyze, admin, webhook, mealplan

logger = logging.getLogger(__name__)

router = APIRouter()
router.include_router(analyze.router,  prefix="/analyze",  tags=["analyze"])
router.include_router(mealplan.router, prefix="/mealplan", tags=["mealplan"])
router.include_router(admin.router,    prefix="/admin",    tags=["admin"])
router.include_router(webhook.router,  prefix="/webhook",  tags=["webhook"])

@router.get("/test", response_model=BaseResponse)
async def test_endpoint():
    """API 테스트 엔드포인트"""
    return BaseResponse(
        message="API가 정상적으로 작동합니다!",
        success=True
    )

@router.get("/info")
async def get_api_info():
    """API 정보 조회"""
    return {
        "api_name": "My Web Template API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": [
            "/api/test",
            "/api/info",
            "/health"
        ]
    }

# TODO: 추가 엔드포인트들을 여기에 구현