# backend/app/services/optimizer.py
"""
전략별 가중치를 지원하는 GA 식단 최적화 서비스
워크플로우에서 전달받은 전략 타입에 따라 최적화 가중치를 조정
"""
import logging
from typing import Dict, Any, Tuple
import pandas as pd

# ga_engine에서 실제 최적화 로직을 가져옴
from app.services.ga_engine import optimize_menu as ga_optimize_menu

logger = logging.getLogger(__name__)

def optimize_menu(paths: Dict[str, str], params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    식단 최적화 메인 함수 (전략별 가중치 지원)
    
    Args:
        paths: CSV 파일 경로들 (price, nutr, cat, pref, cooc)
        params: 최적화 파라미터들 
            - days: 일수
            - budget_won: 예산
            - target_kcal: 목표 칼로리
            - strategy_type: 전략 타입 ('nutrition', 'economic', 'preference')
            - nutrition_weight, cost_weight, preference_weight: 전략별 가중치
    
    Returns:
        Tuple[DataFrame, Dict]: (최적화된 식단표, 요약 정보)
    """
    try:
        logger.info(f"식단 최적화 시작 - 일수: {params.get('days')}, 예산: {params.get('budget_won')}")
        
        # 전략 타입 확인 및 가중치 설정
        strategy_type = params.get('strategy_type', 'nutrition')
        logger.info(f"선택된 전략: {strategy_type}")
        
        # 전략별 기본 가중치 설정 (params에서 우선 적용)
        enhanced_params = _apply_strategy_weights(params.copy(), strategy_type)
        
        # 전략 적용 로그
        logger.info(f"적용된 가중치 - 영양: {enhanced_params.get('nutrition_weight', 0.5):.1f}, "
                   f"비용: {enhanced_params.get('cost_weight', 0.3):.1f}, "
                   f"선호도: {enhanced_params.get('preference_weight', 0.2):.1f}")
        
        # GA 엔진 호출 (가중치가 적용된 파라미터 전달)
        plan_df, summary = ga_optimize_menu(paths=paths, params=enhanced_params)
        
        # 전략 정보를 summary에 추가
        summary['strategy_applied'] = strategy_type
        summary['strategy_weights'] = {
            'nutrition': enhanced_params.get('nutrition_weight', 0.5),
            'cost': enhanced_params.get('cost_weight', 0.3),
            'preference': enhanced_params.get('preference_weight', 0.2)
        }
        
        logger.info(f"식단 최적화 완료 - 총 {len(plan_df)}일 계획 생성 ({strategy_type} 전략 적용)")
        return plan_df, summary
        
    except Exception as e:
        logger.error(f"식단 최적화 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise RuntimeError(f"최적화 처리 중 오류가 발생했습니다: {e}")

def optimize_menu(paths, params):
    strategy_type = params.get('strategy_type', 'nutrition')
    
    if strategy_type == 'nutrition':
        # 영양소 가중치 높임
        fitness_weights = {'nutrition': 0.8, 'cost': 0.1, 'preference': 0.1}
    elif strategy_type == 'economic':
        # 비용 효율성 가중치 높임  
        fitness_weights = {'nutrition': 0.2, 'cost': 0.7, 'preference': 0.1}
    elif strategy_type == 'preference':
        # 선호도 가중치 높임
        fitness_weights = {'nutrition': 0.3, 'cost': 0.2, 'preference': 0.5}

def _apply_strategy_weights(params: Dict[str, Any], strategy_type: str) -> Dict[str, Any]:
    """
    전략 타입에 따라 최적화 가중치를 설정
    
    Args:
        params: 기본 파라미터
        strategy_type: 전략 타입
        
    Returns:
        가중치가 적용된 파라미터
    """
    # 전략별 가중치 정의
    strategy_weights = {
        'nutrition': {
            'nutrition_weight': 0.8,  # 영양소 균형 최우선
            'cost_weight': 0.1,       # 비용은 최소 고려
            'preference_weight': 0.1,  # 선호도는 최소 고려
            'description': '영양 균형 중심'
        },
        'economic': {
            'nutrition_weight': 0.2,  # 기본 영양만 만족
            'cost_weight': 0.7,       # 비용 효율성 최우선
            'preference_weight': 0.1,  # 선호도는 최소 고려
            'description': '경제성 우선'
        },
        'preference': {
            'nutrition_weight': 0.3,  # 기본 영양은 보장
            'cost_weight': 0.2,       # 비용은 적당히 고려
            'preference_weight': 0.5,  # 학생 선호도 최우선
            'description': '선호도 중심'
        },
        'balanced': {
            'nutrition_weight': 0.4,  # 균형잡힌 접근
            'cost_weight': 0.3,
            'preference_weight': 0.3,
            'description': '균형 잡힌 전략'
        }
    }
    
    # 기본값 설정 (알 수 없는 전략의 경우)
    if strategy_type not in strategy_weights:
        logger.warning(f"알 수 없는 전략 타입: {strategy_type}, 영양 전략으로 기본 설정")
        strategy_type = 'nutrition'
    
    weights = strategy_weights[strategy_type]
    
    # 파라미터에 이미 가중치가 설정되어 있다면 그것을 우선 사용
    if 'nutrition_weight' not in params:
        params['nutrition_weight'] = weights['nutrition_weight']
    if 'cost_weight' not in params:
        params['cost_weight'] = weights['cost_weight']  
    if 'preference_weight' not in params:
        params['preference_weight'] = weights['preference_weight']
    
    # 전략 설명 추가
    params['strategy_description'] = weights['description']
    
    # 가중치 검증 (합이 1.0이 되도록)
    total_weight = params['nutrition_weight'] + params['cost_weight'] + params['preference_weight']
    if abs(total_weight - 1.0) > 0.01:  # 오차 허용
        logger.warning(f"가중치 합이 1.0이 아님: {total_weight}, 정규화 수행")
        params['nutrition_weight'] /= total_weight
        params['cost_weight'] /= total_weight
        params['preference_weight'] /= total_weight
    
    return params

# 이전 버전과의 호환성을 위한 래퍼 함수
def optimize_menu_legacy(paths: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    기존 API와의 호환성을 위한 래퍼 함수
    DataFrame 대신 dict를 반환
    """
    try:
        plan_df, summary = optimize_menu(paths, params)
        
        # DataFrame을 dict로 변환
        plan_records = plan_df.to_dict(orient="records")
        
        result = {
            "status": "success",
            "plan": plan_records,
            "summary": summary
        }
        
        return result
        
    except Exception as e:
        logger.error(f"레거시 최적화 함수 실패: {e}")
        raise

# 전략별 최적화 함수들 (편의 함수)
def optimize_nutrition_focused(paths: Dict[str, str], params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """영양 중심 최적화"""
    params['strategy_type'] = 'nutrition'
    return optimize_menu(paths, params)

def optimize_cost_focused(paths: Dict[str, str], params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """비용 효율성 중심 최적화"""
    params['strategy_type'] = 'economic'
    return optimize_menu(paths, params)

def optimize_preference_focused(paths: Dict[str, str], params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """학생 선호도 중심 최적화"""
    params['strategy_type'] = 'preference'
    return optimize_menu(paths, params)

def get_available_strategies() -> Dict[str, Dict[str, Any]]:
    """사용 가능한 전략들과 설명을 반환"""
    return {
        'nutrition': {
            'name': '영양 균형 중심',
            'description': '영양소 균형을 최우선으로 하는 전략',
            'weights': {'nutrition': 0.8, 'cost': 0.1, 'preference': 0.1},
            'best_for': '성장기 학생들의 건강한 발육'
        },
        'economic': {
            'name': '경제성 우선',
            'description': '예산 효율성을 최우선으로 하는 전략',
            'weights': {'nutrition': 0.2, 'cost': 0.7, 'preference': 0.1},
            'best_for': '제한된 예산 내에서 최대한 다양한 메뉴 제공'
        },
        'preference': {
            'name': '선호도 중심',
            'description': '학생 만족도와 섭취율을 최우선으로 하는 전략',
            'weights': {'nutrition': 0.3, 'cost': 0.2, 'preference': 0.5},
            'best_for': '높은 섭취율과 학생 만족도 확보'
        },
        'balanced': {
            'name': '균형 잡힌 전략',
            'description': '영양, 비용, 선호도를 균형있게 고려하는 전략',
            'weights': {'nutrition': 0.4, 'cost': 0.3, 'preference': 0.3},
            'best_for': '전반적으로 균형잡힌 급식 운영'
        }
    }