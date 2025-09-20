# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Optional, List

from pydantic_settings import BaseSettings, SettingsConfigDict

# .../backend (app/core/config.py 기준 두 단계 위)
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # --- pydantic v2 설정 ---
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # ✅ .env에 정의돼 있지만 모델에 없는 키는 무시
    )

    # ===== 공통/서버 환경 =====
    environment: str = "development"
    debug: bool = False
    secret_key: str = "change-me"
    database_url: Optional[str] = "sqlite:///./app.db"

    # CORS - localhost:3000 추가 및 더 관대한 설정
    allowed_origins: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # CORS 추가 설정
    allow_credentials: bool = True
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"]
    allowed_headers: List[str] = ["*"]
    max_age: int = 86400  # 24시간

    # ===== 비전/YOLO 관련 =====
    YOLO_WEIGHTS: Optional[str] = "models/best.pt"
    YOLO_DEVICE: str = "cpu"
    YOLO_IMGSZ: int = 640
    YOLO_CONF: float = 0.5
    YOLO_MAX_DET: int = 20

    # 데이터/미디어 경로
    FOOD_META_PATH: Optional[str] = None
    MEDIA_DIR: str = "media"
    INTAKE_MEDIA_SUBDIR: str = "intake"

    # ===== 식단 최적화 프리셋 플래그 =====
    mealplan_use_preset: bool = True

    # ===== 식단 최적화 CSV 경로(.env 키와 동일) =====
    meal_nutrition_csv: Optional[str] = "backend/data/meal_nutrition.csv"
    meal_price_csv: Optional[str] = "backend/data/meal_price.csv"  
    meal_category_csv: Optional[str] = "backend/data/meal_category.csv"
    meal_student_pref_csv: Optional[str] = "backend/data/student_preference.csv"
    meal_pair_pref_csv: Optional[str] = "backend/data/pair_preference.csv"

    # ===== 타임아웃 설정 (중요!) =====
    request_timeout: int = 300  # 5분
    optimization_timeout: int = 180  # 3분
    keep_alive_timeout: int = 65
    
    # ===== 서버 성능 설정 =====
    workers: int = 1
    worker_connections: int = 1000
    
    # ---------- 유틸 ----------
    @staticmethod
    def resolve_path(p: Optional[str]) -> Optional[str]:
        """상대경로면 backend/ 기준 절대경로로 변환"""
        if not p:
            return None
        q = Path(p)
        if not q.is_absolute():
            q = (BASE_DIR / q).resolve()
        return str(q)


settings = Settings()