# backend/app/services/optimizer.py
"""
GA 식단 최적화 서비스
"""
import logging
from typing import Dict, Any

# ga_engine에서 실제 최적화 로직을 가져옴
from app.services.ga_engine import optimize_menu as ga_optimize_menu

logger = logging.getLogger(__name__)

def optimize_menu(paths: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    식단 최적화 메인 함수
    
    Args:
        paths: CSV 파일 경로들 (price, nutr, cat, pref, cooc)
        params: 최적화 파라미터들 (days, budget_won, target_kcal 등)
    
    Returns:
        Dict containing:
        - status: 최적화 상태
        - plan: 최적화된 식단표 (DataFrame을 dict로 변환)
        - summary: 요약 정보
    """
    try:
        logger.info(f"식단 최적화 시작 - 일수: {params.get('days')}, 예산: {params.get('budget_won')}")
        
        # GA 엔진 호출
        plan_df, summary = ga_optimize_menu(paths=paths, params=params)
        
        # DataFrame을 dict로 변환
        plan_records = plan_df.to_dict(orient="records")
        
        result = {
            "status": "success",
            "plan": plan_records,
            "summary": summary
        }
        
        logger.info(f"식단 최적화 완료 - 총 {len(plan_records)}일 계획 생성")
        return result
        
    except Exception as e:
        logger.error(f"식단 최적화 실패: {e}")
        raise RuntimeError(f"최적화 처리 중 오류가 발생했습니다: {e}")