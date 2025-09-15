# backend/app/api/mealplan.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict
from io import StringIO
import pandas as pd
from fastapi.responses import StreamingResponse

from app.core.config import settings  # ← .env 프리셋 경로 읽어옴
from app.services.ga_engine import optimize_menu  # ← 네 GA 엔진

router = APIRouter()


# --------- 요청 바디 스키마 ---------
class OptimizePaths(BaseModel):
    price: Optional[str] = None
    nutr: Optional[str] = None
    cat: Optional[str] = None
    pref: Optional[str] = None
    cooc: Optional[str] = None

class OptimizeParams(BaseModel):
    days: int = 20
    budget_won: float = 5370.0
    target_kcal: float = 900.0
    carb_range: Optional[tuple[float, float]] = None  # [%]
    prot_range: Optional[tuple[float, float]] = None  # [%]
    fat_range:  Optional[tuple[float, float]] = None  # [%]
    STRICT_BUDGET: Optional[bool] = True

class OptimizeRequest(BaseModel):
    paths: Optional[OptimizePaths] = None
    params: OptimizeParams
    use_preset: Optional[bool] = None  # ← 프리셋 강제 사용 여부


# --------- 내부 유틸 ---------
def _resolve_paths(req_paths: Optional[OptimizePaths], use_preset_flag: Optional[bool]) -> Dict[str, Optional[str]]:
    """요청/프리셋 여부에 따라 실제 경로 dict을 만든다."""
    use_preset = use_preset_flag if use_preset_flag is not None else settings.MEALPLAN_USE_PRESET
    if use_preset:
        return {
            "price": settings.MEAL_PRICE_CSV,
            "nutr": settings.MEAL_NUTR_CSV,
            "cat": settings.MEAL_CATEGORY_CSV,
            "pref": settings.MEAL_STUDENT_PREF_CSV,
            "cooc": settings.MEAL_PAIR_PREF_CSV,
        }
    # 프리셋 미사용이면 price/nutr 필수
    if not req_paths or not req_paths.price or not req_paths.nutr:
        raise HTTPException(400, "paths.price와 paths.nutr가 필요합니다 (또는 use_preset=true)")
    return req_paths.model_dump()


# --------- API ---------
@router.post("/optimize")
def optimize(req: OptimizeRequest):
    try:
        paths = _resolve_paths(req.paths, req.use_preset)
        plan_df, summary = optimize_menu(paths, req.params.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"최적화 실패: {e}")

    return {
        "status": "ok",
        "summary": summary,
        "plan": plan_df.to_dict(orient="records"),
    }


@router.get("/download")
def download_csv(
    # 프리셋으로 바로 내려받기
    use_preset: bool = Query(default=False),
    # 프리셋 미사용 시 개별 경로
    price: Optional[str] = None, nutr: Optional[str] = None,
    cat: Optional[str] = None,   pref: Optional[str] = None, cooc: Optional[str] = None,
    # 기본 파라미터
    days: int = 20, budget_won: float = 5370.0, target_kcal: float = 900.0
):
    try:
        if use_preset or not price or not nutr:
            paths = {
                "price": settings.MEAL_PRICE_CSV,
                "nutr": settings.MEAL_NUTR_CSV,
                "cat": settings.MEAL_CATEGORY_CSV,
                "pref": settings.MEAL_STUDENT_PREF_CSV,
                "cooc": settings.MEAL_PAIR_PREF_CSV,
            }
        else:
            paths = {"price": price, "nutr": nutr, "cat": cat, "pref": pref, "cooc": cooc}

        params = {"days": days, "budget_won": budget_won, "target_kcal": target_kcal}
        plan_df, summary = optimize_menu(paths, params)
    except Exception as e:
        raise HTTPException(400, f"최적화 실패: {e}")

    buff = StringIO()
    plan_df.to_csv(buff, index=False, encoding="utf-8-sig")
    buff.seek(0)
    return StreamingResponse(
        buff,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="mealplan.csv"'}
    )
