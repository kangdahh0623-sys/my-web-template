# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["mealplan"])

class Params(BaseModel):
    days: int
    budget_won: float
    target_kcal: float

class Paths(BaseModel):
    price: str
    nutr: str
    cat: Optional[str] = None
    pref: Optional[str] = None
    cooc: Optional[str] = None

class OptimizePayload(BaseModel):
    params: Params
    use_preset: bool = False
    paths: Optional[Paths] = None

def build_paths_from_settings() -> Dict[str, str]:
    price = settings.resolve_path(settings.MEAL_PRICE_CSV)
    nutr  = settings.resolve_path(settings.MEAL_NUTR_CSV)
    if not price or not nutr:
        raise HTTPException(status_code=500, detail="MEAL_PRICE_CSV/MEAL_NUTR_CSV가 설정되지 않았습니다.")

    d: Dict[str, str] = {"price": price, "nutr": nutr}

    cat  = settings.resolve_path(settings.MEAL_CATEGORY_CSV)
    pref = settings.resolve_path(settings.MEAL_STUDENT_PREF_CSV)
    cooc = settings.resolve_path(settings.MEAL_PAIR_PREF_CSV)
    if cat:  d["cat"]  = cat
    if pref: d["pref"] = pref
    if cooc: d["cooc"] = cooc
    return d

# 최적화를 비동기로 실행하는 함수
async def run_optimization_async(paths: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    """최적화를 별도 스레드에서 실행"""
    import concurrent.futures
    
    def run_optimize():
        try:
            from app.services.optimizer import optimize_menu
            return optimize_menu(paths=paths, params=params)
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            raise e
    
    # ThreadPoolExecutor를 사용하여 블로킹 작업을 비동기로 실행
    with concurrent.futures.ThreadPoolExecutor() as executor:
        try:
            # 타임아웃을 적용하여 최적화 실행
            future = executor.submit(run_optimize)
            result = await asyncio.wait_for(
                asyncio.wrap_future(future), 
                timeout=settings.optimization_timeout - 10  # 여유시간 10초
            )
            return result
        except asyncio.TimeoutError:
            logger.error("Optimization timeout")
            raise HTTPException(
                status_code=408, 
                detail="최적화 시간이 초과되었습니다. 조건을 조정하거나 잠시 후 다시 시도해주세요."
            )
        except Exception as e:
            logger.error(f"Optimization execution error: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"최적화 실행 중 오류가 발생했습니다: {str(e)}"
            )

@router.post("/mealplan/optimize")
async def optimize_mealplan(payload: OptimizePayload, background_tasks: BackgroundTasks):
    logger.info(f"Optimization request: days={payload.params.days}, budget={payload.params.budget_won}, kcal={payload.params.target_kcal}")
    
    try:
        # 1) 경로 소스 결정
        if payload.use_preset:
            paths = build_paths_from_settings()
        elif payload.paths:
            paths = payload.paths.dict()
            # None 값들을 제거
            paths = {k: v for k, v in paths.items() if v is not None}
        else:
            paths = {}
        
        # 2) 필수 검증
        if not paths.get("price") or not paths.get("nutr"):
            raise HTTPException(
                status_code=400, 
                detail="paths.price / paths.nutr 필요 (또는 use_preset=true)"
            )
        
        # 3) 파라미터 검증
        if payload.params.days <= 0 or payload.params.days > 365:
            raise HTTPException(status_code=400, detail="days는 1-365 사이여야 합니다.")
        
        if payload.params.budget_won <= 0:
            raise HTTPException(status_code=400, detail="budget_won은 0보다 커야 합니다.")
            
        if payload.params.target_kcal <= 0:
            raise HTTPException(status_code=400, detail="target_kcal은 0보다 커야 합니다.")
        
        logger.info(f"Starting optimization with paths: {list(paths.keys())}")
        
        # 4) 실제 최적화 호출 (비동기)
        result = await run_optimization_async(
            paths=paths, 
            params=payload.params.dict()
        )
        
        logger.info(f"Optimization completed successfully. Result keys: {list(result.keys()) if result else 'None'}")
        
        # 5) 결과 검증
        if not result:
            raise HTTPException(
                status_code=500, 
                detail="최적화 결과가 없습니다. 조건을 확인해주세요."
            )
            
        # plan이 없거나 빈 경우 처리
        if not result.get("plan"):
            result["plan"] = []
            logger.warning("Empty plan returned from optimizer")
        
        return result
        
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except asyncio.TimeoutError:
        logger.error("Request timeout in optimize_mealplan")
        raise HTTPException(
            status_code=408, 
            detail="요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
        )
    except ImportError as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="최적화 모듈을 찾을 수 없습니다. 서버 설정을 확인해주세요."
        )
    except Exception as e:
        logger.error(f"Unexpected error in optimize_mealplan: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"최적화 중 오류가 발생했습니다: {str(e)}"
        )