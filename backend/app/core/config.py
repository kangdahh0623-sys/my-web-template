# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, List

from pydantic import field_validator
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
    yolo_weights: Optional[str] = "models/best.pt"
    yolo_device: str = "cpu"
    yolo_imgsz: int = 640
    yolo_conf: float = 0.5
    yolo_max_det: int = 20

    # 데이터/미디어 경로
    food_meta_path: Optional[str] = None
    media_dir: str = "media"
    intake_media_subdir: str = "intake"

    # ===== 식단 최적화 프리셋 플래그 =====
    mealplan_use_preset: bool = True

    # ===== 식단 최적화 CSV 경로(.env 키와 동일) =====
    MEAL_PRICE_CSV: Optional[str] = None
    MEAL_NUTR_CSV: Optional[str] = None
    MEAL_CATEGORY_CSV: Optional[str] = None
    MEAL_STUDENT_PREF_CSV: Optional[str] = None
    MEAL_PAIR_PREF_CSV: Optional[str] = None

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

    # ---------- 파서/밸리데이터 ----------
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_allowed_origins(cls, v):
        # .env에서 '["...","..."]' 형태면 JSON으로 파싱, 콤마 구분 문자열도 허용
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @field_validator("allowed_methods", "allowed_headers", mode="before")
    @classmethod
    def _parse_list_fields(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @field_validator("debug", "mealplan_use_preset", "allow_credentials", mode="before")
    @classmethod
    def _parse_bool(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "y", "on"}
        return bool(v)

    @field_validator("yolo_imgsz", "yolo_max_det", "max_age", "request_timeout", "optimization_timeout", "keep_alive_timeout", "workers", "worker_connections", mode="before")
    @classmethod
    def _parse_int(cls, v):
        try:
            return int(v)
        except Exception:
            return v

    @field_validator("yolo_conf", mode="before")
    @classmethod
    def _parse_float(cls, v):
        try:
            return float(v)
        except Exception:
            return v


settings = Settings()