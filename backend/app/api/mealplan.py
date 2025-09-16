# backend/app/api/mealplan.py
from typing import Optional, Dict, Any
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()   # prefix 없음
@router.post("/optimize")

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
    price = settings.resolve_path(getattr(settings, "MEAL_PRICE_CSV", None))
    nutr  = settings.resolve_path(getattr(settings, "MEAL_NUTR_CSV", None))
    if not price or not nutr:
        raise HTTPException(status_code=500, detail="MEAL_PRICE_CSV/MEAL_NUTR_CSV가 설정되지 않았습니다.")
    d = {"price": price, "nutr": nutr}
    for key_env in ("MEAL_CATEGORY_CSV","MEAL_STUDENT_PREF_CSV","MEAL_PAIR_PREF_CSV"):
        p = settings.resolve_path(getattr(settings, key_env, None))
        if p: d[key_env.replace("MEAL_","").replace("_CSV","").lower()] = p
    return d

async def run_optimization_async(paths: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    import concurrent.futures
    def run_optimize():
        from app.services.optimizer import optimize_menu
        return optimize_menu(paths=paths, params=params)
    with concurrent.futures.ThreadPoolExecutor() as ex:
        try:
            fut = ex.submit(run_optimize)
            timeout_sec = int(getattr(settings, "optimization_timeout", 120)) - 10
            return await asyncio.wait_for(asyncio.wrap_future(fut), timeout=timeout_sec)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="최적화 시간이 초과되었습니다.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"최적화 실행 오류: {e}")

@router.post("/optimize")
async def optimize_mealplan(payload: OptimizePayload):
    paths = (
        build_paths_from_settings() if payload.use_preset
        else {k:v for k,v in (payload.paths.dict() if payload.paths else {}).items() if v is not None}
    )
    if not paths.get("price") or not paths.get("nutr"):
        raise HTTPException(status_code=400, detail="paths.price / paths.nutr 필요 (또는 use_preset=true)")
    if payload.params.days <= 0 or payload.params.days > 365:
        raise HTTPException(status_code=400, detail="days는 1-365 사이여야 합니다.")
    if payload.params.budget_won <= 0:
        raise HTTPException(status_code=400, detail="budget_won은 0보다 커야 합니다.")
    if payload.params.target_kcal <= 0:
        raise HTTPException(status_code=400, detail="target_kcal은 0보다 커야 합니다.")

    result = await run_optimization_async(paths=paths, params=payload.params.dict())
    if not result:
        raise HTTPException(status_code=500, detail="최적화 결과가 없습니다.")

    return {
        "status": result.get("status", "ok"),
        "summary": result.get("summary", {}),
        "plan": result.get("plan", []) or [],
    }
