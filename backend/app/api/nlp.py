# backend/app/api/nlp.py
"""
자연어 파라미터 변경 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import logging

from app.services.natural_language import nl_processor
from app.models.schemas import BaseResponse

logger = logging.getLogger(__name__)
router = APIRouter()

class NLPRequest(BaseModel):
    """자연어 처리 요청"""
    natural_input: str = Field(..., min_length=1, max_length=500,
                              description="자연어 입력")
    current_params: Dict[str, Any] = Field(..., description="현재 파라미터 값들")

class NLPResponse(BaseResponse):
    """자연어 처리 응답"""
    updated_params: Dict[str, Any]
    change_log: List[str]
    suggestions: List[str]

@router.post("/process", response_model=NLPResponse)
async def process_natural_language(request: NLPRequest):
    """
    자연어 입력을 처리하여 파라미터 업데이트
    
    예시:
    - "가격 500원 올려줘" → budget += 500
    - "칼로리를 900으로 설정해줘" → calories = 900
    - "일수를 5일 늘려줘" → days += 5
    """
    try:
        logger.info(f"자연어 처리 요청: '{request.natural_input}'")
        logger.info(f"현재 파라미터: {request.current_params}")
        
        # 자연어 처리
        updated_params, change_log = nl_processor.process_input(
            request.natural_input,
            request.current_params
        )
        
        # 제안 예시 가져오기
        suggestions = nl_processor.get_suggestion_examples()
        
        logger.info(f"처리 완료 - 변경 로그: {change_log}")
        
        return NLPResponse(
            message="자연어 처리 완료",
            success=True,
            updated_params=updated_params,
            change_log=change_log,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"자연어 처리 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"자연어 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/examples")
async def get_examples():
    """자연어 입력 예시 반환"""
    return {
        "examples": nl_processor.get_suggestion_examples(),
        "supported_parameters": [
            "예산/가격 (원)",
            "칼로리 (kcal)", 
            "일수/기간 (일)",
            "단백질 (g)",
            "탄수화물 (g)",
            "지방 (g)",
            "나트륨 (mg)"
        ],
        "supported_actions": [
            "올려줘/높여줘/증가 (증가)",
            "내려줘/낮춰줘/감소 (감소)", 
            "~로 설정/~을 맞춰 (설정)",
            "조금/약간 (소량 변경)",
            "많이/대폭 (대량 변경)",
            "두배/절반 (비율 변경)"
        ]
    }

@router.get("/")
async def nlp_root():
    """NLP API 루트"""
    return {
        "message": "Natural Language Processing API",
        "version": "1.0.0",
        "endpoints": {
            "process": "POST /process - 자연어 파라미터 변경",
            "examples": "GET /examples - 사용 예시"
        }
    }