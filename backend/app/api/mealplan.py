# backend/app/api/mealplan.py (디버깅 강화)
from typing import Optional, Dict, Any, List
import asyncio
import logging
import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.config import settings

# 더 상세한 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class Params(BaseModel):
    days: int = Field(..., ge=1, le=365, description="식단 생성 일수")
    budget_won: float = Field(..., gt=0, description="1인당 예산 (원)")
    target_kcal: float = Field(..., gt=0, description="목표 칼로리")

class Paths(BaseModel):
    price: str = Field(..., description="가격 CSV 파일 경로")
    nutr: str = Field(..., description="영양소 CSV 파일 경로")
    cat: Optional[str] = Field(None, description="카테고리 CSV 파일 경로")
    pref: Optional[str] = Field(None, description="학생 선호도 CSV 파일 경로")
    cooc: Optional[str] = Field(None, description="메뉴 조합 선호도 CSV 파일 경로")

class OptimizePayload(BaseModel):
    params: Params
    use_preset: bool = Field(default=False, description="서버 프리셋 경로 사용 여부")
    paths: Optional[Paths] = Field(None, description="CSV 파일 경로들")

def build_paths_from_settings() -> Dict[str, str]:
    """환경변수에서 CSV 파일 경로들을 읽어서 반환"""
    try:
        logger.info("프리셋 경로 구성 시작...")
        
        # 소문자로 된 환경변수명 사용
        price = settings.resolve_path(getattr(settings, "meal_price_csv", None))
        nutr = settings.resolve_path(getattr(settings, "meal_nutr_csv", None))
        
        logger.info(f"Price CSV 경로: {price}")
        logger.info(f"Nutrition CSV 경로: {nutr}")
        
        if not price or not nutr:
            raise HTTPException(
                status_code=500, 
                detail="필수 CSV 파일 경로가 설정되지 않았습니다. MEAL_PRICE_CSV와 MEAL_NUTR_CSV를 확인해주세요."
            )
        
        import os
        if not os.path.exists(price):
            raise HTTPException(status_code=500, detail=f"가격 CSV 파일이 존재하지 않습니다: {price}")
        if not os.path.exists(nutr):
            raise HTTPException(status_code=500, detail=f"영양소 CSV 파일이 존재하지 않습니다: {nutr}")
        
        paths = {"price": price, "nutr": nutr}
        
        # 선택적 파일들
        optional_files = {
            "meal_category_csv": "cat",
            "meal_student_pref_csv": "pref", 
            "meal_pair_pref_csv": "cooc"
        }
        
        for env_key, path_key in optional_files.items():
            file_path = settings.resolve_path(getattr(settings, env_key, None))
            if file_path and os.path.exists(file_path):
                paths[path_key] = file_path
                logger.info(f"{path_key} 파일 추가: {file_path}")
        
        logger.info(f"최종 프리셋 경로: {paths}")
        return paths
        
    except Exception as e:
        logger.error(f"프리셋 경로 구성 실패: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"설정 파일 경로 오류: {e}")

async def run_optimization_async(paths: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    """비동기로 최적화 실행"""
    import concurrent.futures
    
    def run_optimize():
        try:
            logger.info(f"최적화 시작 - 파라미터: {params}")
            logger.info(f"사용할 파일 경로: {paths}")
            
            from app.services.optimizer import optimize_menu
            result = optimize_menu(paths=paths, params=params)
            
            logger.info(f"최적화 완료 - 결과 타입: {type(result)}")
            if isinstance(result, tuple) and len(result) >= 2:
                plan_df, summary = result
                logger.info(f"Plan DataFrame 크기: {len(plan_df) if hasattr(plan_df, '__len__') else 'N/A'}")
                logger.info(f"Summary: {summary}")
                
                # DataFrame을 dict로 변환
                plan_records = plan_df.to_dict(orient="records") if hasattr(plan_df, 'to_dict') else []
                
                return {
                    "status": "success",
                    "plan": plan_records,
                    "summary": summary
                }
            else:
                logger.warning(f"예상치 못한 결과 형식: {result}")
                return result
            
        except Exception as e:
            logger.error(f"최적화 실행 중 오류: {e}")
            logger.error(traceback.format_exc())
            raise
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        try:
            future = executor.submit(run_optimize)
            timeout_sec = getattr(settings, "optimization_timeout", 180)
            logger.info(f"최적화 타임아웃: {timeout_sec}초")
            
            result = await asyncio.wait_for(
                asyncio.wrap_future(future), 
                timeout=timeout_sec
            )
            return result
        except asyncio.TimeoutError:
            logger.error("최적화 시간 초과")
            raise HTTPException(status_code=408, detail="최적화 시간이 초과되었습니다.")
        except Exception as e:
            logger.error(f"최적화 비동기 실행 오류: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"최적화 실행 오류: {e}")

@router.post("/optimize")
async def optimize_mealplan(payload: OptimizePayload):
    """식단 최적화 API"""
    try:
        logger.info("="*50)
        logger.info(f"새로운 최적화 요청 수신")
        logger.info(f"use_preset: {payload.use_preset}")
        logger.info(f"파라미터: {payload.params.dict()}")
        
        # 특별한 검증: 일수가 너무 클 때 경고
        if payload.params.days > 30:
            logger.warning(f"큰 일수 요청: {payload.params.days}일 - 처리 시간이 오래 걸릴 수 있습니다")
        
        # 경로 설정
        if payload.use_preset:
            paths = build_paths_from_settings()
        else:
            if not payload.paths:
                raise HTTPException(
                    status_code=400, 
                    detail="use_preset=false일 때는 paths가 필요합니다."
                )
            paths = {k: v for k, v in payload.paths.dict().items() if v is not None}
        
        # 필수 경로 확인
        if not paths.get("price") or not paths.get("nutr"):
            raise HTTPException(
                status_code=400, 
                detail="price와 nutr 경로는 필수입니다."
            )
        
        # 최적화 실행
        logger.info("최적화 프로세스 시작...")
        result = await run_optimization_async(
            paths=paths, 
            params=payload.params.dict()
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="최적화 결과가 없습니다.")
        
        # 응답 형식 정규화
        response = {
            "status": result.get("status", "success"),
            "summary": result.get("summary", {}),
            "plan": result.get("plan", [])
        }
        
        logger.info(f"최적화 성공 - 계획 수: {len(response['plan'])}")
        
        # 응답 데이터 샘플 로그
        if response['plan']:
            logger.info(f"첫 번째 계획 샘플: {response['plan'][0]}")
            logger.info(f"마지막 계획 샘플: {response['plan'][-1]}")
        
        logger.info("="*50)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"식단 최적화 처리 중 예상치 못한 오류: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"최적화 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/")
async def mealplan_root():
    """식단 계획 API 루트"""
    return {
        "message": "Meal Planning API",
        "version": "1.0.0",
        "endpoints": {
            "optimize": "POST /optimize - 식단 최적화"
        },
        "preset_available": bool(getattr(settings, "meal_price_csv", None) and 
                                getattr(settings, "meal_nutr_csv", None))
    }

@router.get("/status")
async def mealplan_status():
    """식단 계획 API 상태 확인"""
    try:
        preset_paths = build_paths_from_settings()
        return {
            "status": "healthy",
            "preset_paths": preset_paths,
            "csv_files_ready": True
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "csv_files_ready": False
        }