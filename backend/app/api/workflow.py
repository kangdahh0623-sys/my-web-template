# backend/app/api/workflow.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import re
from app.core.config import settings

# 실제 CSV 데이터 기반 에이전트 임포트
from app.services.workflow_agents import (
    generate_strategies_from_request,
    analyze_strategy_with_agents,
    parse_natural_language_params
)

logger = logging.getLogger(__name__)
router = APIRouter()

def get_real_data_paths():
    return {
        'nutrition': settings.resolve_path(settings.meal_nutrition_csv),
        'price': settings.resolve_path(settings.meal_price_csv),
        'category': settings.resolve_path(settings.meal_category_csv),
        'student_pref': settings.resolve_path(settings.meal_student_pref_csv),
        'pair_pref': settings.resolve_path(settings.meal_pair_pref_csv)
    }

def get_real_data_paths() -> Dict[str, str]:
    """실제 CSV 파일 경로들을 반환"""
    try:
        paths = {}
        
        # 필수 파일들
        nutrition_path = settings.resolve_path(getattr(settings, 'meal_nutrition_csv', 'backend/data/meal_nutrition.csv'))
        price_path = settings.resolve_path(getattr(settings, 'meal_price_csv', 'backend/data/meal_price.csv'))
        
        if not nutrition_path or not price_path:
            raise ValueError("필수 CSV 파일 경로가 설정되지 않았습니다.")
        
        paths['nutrition'] = nutrition_path
        paths['price'] = price_path
        
        # 선택적 파일들
        optional_files = {
            'meal_category_csv': 'category',
            'meal_student_pref_csv': 'student_pref',
            'meal_pair_pref_csv': 'pair_pref'
        }
        
        for setting_key, path_key in optional_files.items():
            file_path = settings.resolve_path(getattr(settings, setting_key, None))
            if file_path:
                paths[path_key] = file_path
                logger.info(f"{path_key} 파일 경로 설정: {file_path}")
        
        logger.info(f"실제 CSV 데이터 경로 설정 완료: {paths}")
        return paths
        
    except Exception as e:
        logger.error(f"CSV 경로 설정 실패: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 파일 경로 오류: {e}")

class UserRequest(BaseModel):
    user_request: str = Field(..., description="사용자의 자연어 요청")

class Alternative(BaseModel):
    id: int
    title: str
    description: str
    strategy_type: str  # 'nutrition', 'economic', 'preference'
    estimated_cost: float
    target_calories: float
    features: List[str]
    highlight: str
    nutrition_score: Optional[float] = None
    economic_score: Optional[float] = None
    preference_score: Optional[float] = None
    feasibility_score: Optional[float] = None

class AgentAnalysisRequest(BaseModel):
    alternative_id: int
    params: Dict[str, Any]

class AgentAnalysisResponse(BaseModel):
    nutrition_agent: float
    economic_agent: float
    student_agent: float
    operation_agent: float
    consensus: str
    recommendation: str

class NaturalLanguageRequest(BaseModel):
    natural_text: str
    current_params: Dict[str, Any]

class WorkflowOptimizeRequest(BaseModel):
    use_preset: bool = True
    strategy_type: str
    strategy_id: int
    params: Dict[str, Any]

@router.post("/generate-alternatives")
async def generate_alternatives(request: UserRequest):
    """실제 CSV 데이터를 분석하여 3가지 전략 대안 생성"""
    try:
        logger.info(f"실제 CSV 기반 사용자 요청 분석: {request.user_request}")
        
        # 실제 CSV 데이터 경로 확인
        data_paths = get_real_data_paths()
        logger.info(f"사용할 데이터 파일들: {data_paths}")
        
        # 실제 CSV 데이터 기반으로 전략들 생성
        alternatives = await generate_strategies_from_request(request.user_request)
        
        logger.info(f"실제 데이터 기반 대안 생성 완료: {len(alternatives)}개")
        return {"alternatives": alternatives}
        
    except Exception as e:
        logger.error(f"실제 데이터 기반 대안 생성 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"CSV 데이터 분석 중 오류: {str(e)}")

@router.post("/agent-analysis")
async def agent_analysis(request: AgentAnalysisRequest) -> AgentAnalysisResponse:
    """실제 데이터 기반 멀티 에이전트 분석 수행"""
    try:
        logger.info(f"실제 데이터 기반 Agent 분석 시작: alternative_id={request.alternative_id}")
        
        # 실제 CSV 데이터로 멀티 에이전트 분석
        analysis = await analyze_strategy_with_agents(
            request.alternative_id, 
            request.params
        )
        
        logger.info(f"Agent 분석 완료: {analysis}")
        return analysis
        
    except Exception as e:
        logger.error(f"Agent 분석 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Agent 분석 중 오류: {str(e)}")

@router.post("/parse-natural-language")
async def parse_natural_language(request: NaturalLanguageRequest):
    """자연어를 파싱하여 파라미터 변경"""
    try:
        logger.info(f"자연어 파싱: {request.natural_text}")
        
        result = await parse_natural_language_params(
            request.natural_text,
            request.current_params
        )
        
        logger.info(f"자연어 파싱 결과: {result}")
        return result
        
    except Exception as e:
        logger.error(f"자연어 파싱 실패: {e}")
        raise HTTPException(status_code=500, detail=f"자연어 파싱 중 오류: {str(e)}")

class NaturalLanguageRequest(BaseModel):
    natural_text: str
    current_params: Dict[str, Any]

@router.post("/optimize")
async def optimize_with_strategy(request: WorkflowOptimizeRequest):
    """실제 CSV 데이터와 전략을 기반으로 메뉴 최적화 수행"""
    try:
        logger.info(f"실제 데이터 기반 전략 최적화: {request.strategy_type}")
        
        # 전략별 가중치 설정
        strategy_weights = {
            'nutrition': {'nutrition_weight': 0.8, 'cost_weight': 0.1, 'preference_weight': 0.1},
            'economic': {'nutrition_weight': 0.2, 'cost_weight': 0.7, 'preference_weight': 0.1},
            'preference': {'nutrition_weight': 0.3, 'cost_weight': 0.2, 'preference_weight': 0.5}
        }
        
        weights = strategy_weights.get(request.strategy_type, strategy_weights['nutrition'])
        
        # 실제 CSV 경로 사용 (기존 mealplan API와 호환)
        from app.api.mealplan import build_paths_from_settings
        
        try:
            # 기존 CSV 경로 시스템 사용
            paths = build_paths_from_settings()
        except Exception:
            # fallback: 워크플로우 전용 경로 사용
            data_paths = get_real_data_paths()
            paths = {
                'price': data_paths['price'],
                'nutr': data_paths['nutrition']
            }
            if 'category' in data_paths:
                paths['cat'] = data_paths['category']
            if 'student_pref' in data_paths:
                paths['pref'] = data_paths['student_pref']
            if 'pair_pref' in data_paths:
                paths['cooc'] = data_paths['pair_pref']
        
        # 전략이 적용된 파라미터로 최적화
        enhanced_params = {
            **request.params,
            **weights,  # 전략별 가중치 추가
            'strategy_type': request.strategy_type
        }
        
        logger.info(f"최적화 파라미터: {enhanced_params}")
        logger.info(f"사용할 CSV 파일들: {paths}")
        
        # 실제 최적화 실행 (기존 GA 알고리즘 활용)
        from app.services.optimizer import optimize_menu
        plan_df, summary = optimize_menu(paths=paths, params=enhanced_params)
        
        # DataFrame을 dict로 변환
        plan_records = plan_df.to_dict(orient="records") if hasattr(plan_df, 'to_dict') else []
        
        logger.info(f"실제 CSV 기반 최적화 완료: {len(plan_records)}개 메뉴")
        
        return {
            "status": "success",
            "plan": plan_records,
            "summary": summary,
            "strategy_applied": f"{request.strategy_type} 전략이 실제 CSV 데이터에 적용되었습니다.",
            "data_source": f"실제 파일: {list(paths.values())}"
        }
        
    except Exception as e:
        logger.error(f"실제 데이터 기반 최적화 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"CSV 기반 최적화 중 오류: {str(e)}")

@router.get("/")
async def workflow_root():
    """워크플로우 API 루트 - 실제 데이터 연결 상태 확인"""
    try:
        data_paths = get_real_data_paths()
        
        # 파일 존재 여부 확인
        import os
        file_status = {}
        for key, path in data_paths.items():
            file_status[key] = {
                "path": path,
                "exists": os.path.exists(path)
            }
        
        return {
            "message": "실제 CSV 기반 Workflow API",
            "version": "2.0.0",
            "endpoints": {
                "generate-alternatives": "POST - 실제 CSV 데이터 기반 AI 전략 대안 생성",
                "agent-analysis": "POST - 실제 데이터 기반 멀티 에이전트 분석",
                "parse-natural-language": "POST - 자연어 파라미터 파싱",
                "optimize": "POST - 실제 CSV 데이터 + 전략 기반 메뉴 최적화"
            },
            "data_files": file_status,
            "ready": all(status["exists"] for status in file_status.values())
        }
    except Exception as e:
        return {
            "message": "Workflow API - 설정 오류",
            "error": str(e),
            "ready": False
        }

@router.get("/status")
async def workflow_status():
    """실제 CSV 데이터 연결 상태 확인"""
    try:
        data_paths = get_real_data_paths()
        
        import os
        status_info = {
            "csv_files_connected": True,
            "files": {}
        }
        
        for key, path in data_paths.items():
            exists = os.path.exists(path)
            if exists:
                try:
                    import pandas as pd
                    df = pd.read_csv(path)
                    file_info = {
                        "path": path,
                        "exists": True,
                        "rows": len(df),
                        "columns": list(df.columns)
                    }
                except Exception as e:
                    file_info = {
                        "path": path,
                        "exists": True,
                        "error": f"읽기 오류: {str(e)}"
                    }
            else:
                file_info = {
                    "path": path,
                    "exists": False
                }
                status_info["csv_files_connected"] = False
            
            status_info["files"][key] = file_info
        
        return status_info
        
    except Exception as e:
        return {
            "csv_files_connected": False,
            "error": str(e)
        }