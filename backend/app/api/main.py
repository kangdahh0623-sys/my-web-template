# backend/app/api/main.py
# -*- coding: utf-8 -*-
from fastapi import APIRouter

# 메인 API 라우터 생성
router = APIRouter()

@router.get("/")
async def api_root():
    """API 루트 엔드포인트"""
    return {
        "message": "API is running",
        "version": "1.0.0",
        "status": "ok"
    }

@router.get("/status")
async def api_status():
    """API 상태 확인"""
    return {
        "status": "healthy",
        "message": "All systems operational"
    }