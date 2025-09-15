# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import settings

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

@router.post("/mealplan/optimize")
async def optimize_mealplan(payload: OptimizePayload):
    # 1) 경로 소스 결정
    paths = build_paths_from_settings() if payload.use_preset else (payload.paths.dict() if payload.paths else {})
    # 2) 필수 검증
    if not paths.get("price") or not paths.get("nutr"):
        raise HTTPException(status_code=400, detail="paths.price / paths.nutr 필요 (또는 use_preset=true)")
    # 3) 실제 최적화 호출
    from app.services.optimizer import optimize_menu  # 실제 위치에 맞추세요
    try:
        return optimize_menu(paths=paths, params=payload.params.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"optimize failed: {e}")
