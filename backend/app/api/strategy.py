# backend/app/api/strategy.py
"""
LLM 전략 생성 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.services.llm_strategy import llm_strategy_service, MenuAlternative
from app.models.schemas import BaseResponse

logger = logging.getLogger(__name__)
router = APIRouter()

class StrategyRequest(BaseModel):
    """전략 생성 요청"""
    user_request: str = Field(..., min_length=10, max_length=1000, 
                             description="사용자 요구사항")
    context: Optional[Dict[str, Any]] = Field(default=None, 
                                            description="추가 컨텍스트 정보")

class AlternativeResponse(BaseModel):
    """메뉴 전략 응답"""
    id: int
    title: str
    description: str
    estimated_cost: float
    target_calories: float
    features: List[str]
    pros: List[str]
    cons: List[str]
    risks: List[str]
    strategy_params: Dict[str, Any]

class StrategyResponse(BaseResponse):
    """전략 생성 응답"""
    alternatives: List[AlternativeResponse]
    analysis: Dict[str, Any]

class ComparisonRequest(BaseModel):
    """대안 비교 분석 요청"""
    selected_alternatives: List[int] = Field(..., min_items=1, max_items=5)
    comparison_criteria: Optional[List[str]] = Field(default=["cost", "nutrition", "feasibility"])

class ComparisonResponse(BaseModel):
    """RPA 비교 분석 응답"""
    comparison_table: List[Dict[str, Any]]
    recommendations: Dict[str, Any]
    risk_assessment: Dict[str, Any]

@router.post("/generate", response_model=StrategyResponse)
async def generate_alternatives(request: StrategyRequest):
    """
    사용자 요청을 기반으로 5가지 메뉴 전략 대안 생성
    """
    try:
        logger.info(f"전략 생성 요청: {request.user_request}")
        
        # LLM 서비스를 통한 대안 생성
        alternatives = llm_strategy_service.generate_alternatives_with_llm(request.user_request)
        
        # 사용자 요청 분석 결과
        analysis = llm_strategy_service.analyze_user_request(request.user_request)
        
        # 응답 데이터 변환
        alternative_responses = []
        for alt in alternatives:
            alternative_responses.append(AlternativeResponse(
                id=alt.id,
                title=alt.title,
                description=alt.description,
                estimated_cost=alt.estimated_cost,
                target_calories=alt.target_calories,
                features=alt.features,
                pros=alt.pros,
                cons=alt.cons,
                risks=alt.risks,
                strategy_params=alt.strategy_params
            ))
        
        logger.info(f"전략 생성 완료: {len(alternative_responses)}개 대안")
        
        return StrategyResponse(
            message="전략 대안 생성 완료",
            success=True,
            alternatives=alternative_responses,
            analysis=analysis
        )
        
    except Exception as e:
        logger.error(f"전략 생성 실패: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"전략 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/compare", response_model=ComparisonResponse)
async def compare_alternatives(request: ComparisonRequest):
    """
    선택된 대안들을 RPA 방식으로 비교 분석
    """
    try:
        logger.info(f"대안 비교 요청: {request.selected_alternatives}")
        
        # Agent-based 비교 테이블 생성 (다중 에이전트 분석)
        comparison_table = []
        
        # 영양사 에이전트, 경제 에이전트, 학생 에이전트, 운영 에이전트의 종합 분석
        for alt_id in request.selected_alternatives:
            # 각 에이전트별 점수 계산 (Mock)
            nutritionist_score = 90 - (alt_id * 2)  # 영양사 관점
            economist_score = 85 - (alt_id * 5)     # 경제성 관점  
            student_score = 70 + (alt_id * 5)       # 학생 만족도 관점
            operator_score = 80 - (alt_id * 3)      # 운영 효율성 관점
            
            comparison_row = {
                "id": alt_id,
                "title": f"전략 {alt_id}",
                "nutritionist_agent_score": nutritionist_score,
                "economist_agent_score": economist_score,
                "student_agent_score": student_score,
                "operator_agent_score": operator_score,
                "综合_score": round((nutritionist_score + economist_score + student_score + operator_score) / 4, 1),
                "feasibility": "높음" if alt_id <= 3 else "보통",
                "risk_level": "낮음" if alt_id <= 2 else "보통",
                "implementation_difficulty": "쉬움" if alt_id <= 2 else "보통",
                "budget_compliance": "준수" if alt_id != 5 else "초과"
            }
            comparison_table.append(comparison_row)
        
        # Agent-based 추천 결과 생성
        recommendations = {
            "top_choice": request.selected_alternatives[0],
            "agent_consensus": "영양사 에이전트와 경제 에이전트가 동시에 추천",
            "reasons": [
                "영양사 에이전트: 영양 균형이 우수함",
                "경제 에이전트: 예산 준수율이 가장 높음", 
                "운영 에이전트: 구현 가능성이 높음"
            ],
            "consideration_points": [
                "학생 에이전트: 만족도 추가 고려 필요",
                "모든 에이전트: 계절적 요인 반영 검토"
            ]
        }
        
        # 위험 평가 (다중 에이전트 관점)
        risk_assessment = {
            "high_risks": [],
            "medium_risks": ["식재료 가격 변동 (경제 에이전트)", "조리 인력 부족 (운영 에이전트)"],
            "low_risks": ["학생 적응도 (학생 에이전트)", "메뉴 다양성 (영양사 에이전트)"],
            "mitigation_strategies": [
                "경제 에이전트 제안: 대체 식재료 목록 준비",
                "운영 에이전트 제안: 단계적 메뉴 도입",
                "학생 에이전트 제안: 정기적 만족도 조사",
                "영양사 에이전트 제안: 영양소 모니터링 강화"
            ]
        }
        
        # Agent 통찰력 추가
        agent_insights = {
            "nutritionist_agent": {
                "priority": "영양 균형 및 성장 발육 지원",
                "key_metrics": ["단백질 함량", "비타민/무기질", "칼로리 밀도"],
                "recommendation": "영양소 다양성 확보가 최우선"
            },
            "economist_agent": {
                "priority": "비용 효율성 및 예산 준수",
                "key_metrics": ["1인당 비용", "식재료 단가", "운영비 절감"],
                "recommendation": "시장 가격 변동성을 고려한 유연한 예산 운영"
            },
            "student_agent": {
                "priority": "기호도 및 만족도 향상",
                "key_metrics": ["선호도 점수", "잔반량", "재구매 의향"],
                "recommendation": "트렌드를 반영한 메뉴 개발이 필요"
            },
            "operator_agent": {
                "priority": "조리 효율성 및 운영 안정성",
                "key_metrics": ["조리 시간", "인력 투입", "설비 활용도"],
                "recommendation": "표준화된 조리법으로 품질 일관성 확보"
            }
        }
        
        return ComparisonResponse(
            comparison_table=comparison_table,
            recommendations=recommendations,
            risk_assessment=risk_assessment,
            agent_insights=agent_insights
        )
        
    except Exception as e:
        logger.error(f"대안 비교 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"대안 비교 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/")
async def strategy_root():
    """전략 API 루트"""
    return {
        "message": "Menu Strategy API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "POST /generate - 전략 대안 생성",
            "compare": "POST /compare - 대안 비교 분석"
        }
    }

@router.get("/status")
async def strategy_status():
    """전략 API 상태 확인"""
    return {
        "status": "healthy",
        "llm_available": llm_strategy_service.api_key is not None,
        "service_ready": True
    }