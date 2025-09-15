# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 기본
    APP_NAME: str = "My Web Template"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # 서버
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS (개발용)
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]

    # DB/보안 (필요시 변경)
    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "change-this-secret-key"

    # ===== YOLO / Intake 설정 추가 =====
    # 가중치 경로(상대/절대 모두 가능)
    YOLO_WEIGHTS: str = "models/best.pt"
    # 네가 쓰는 외부 영양/밀도 사전 폴더 (없으면 빈 문자열)
    FOOD_META_PATH: str = ""
    # 미디어(시각화 이미지) 저장 위치
    MEDIA_DIR: str = "media"
    INTAKE_MEDIA_SUBDIR: str = "intake"

    # 기본 추론 파라미터(필요 시 사용)
    YOLO_DEVICE: str = "cpu"
    YOLO_IMGSZ: int = 224
    YOLO_CONF: float = 0.5
    YOLO_MAX_DET: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    MEAL_PRICE_CSV: str = "data/price.csv"
    MEAL_NUTR_CSV: str = "data/nutr.csv"
    MEAL_CATEGORY_CSV: Optional[str] = None
    MEAL_STUDENT_PREF_CSV: Optional[str] = None
    MEAL_PAIR_PREF_CSV: Optional[str] = None

    MEALPLAN_USE_PRESET: bool = True  # 기본 프리셋 사용

    class Config:
        env_file = ".env"
        case_sensitive = True
# 전역 설정 인스턴스
settings = Settings()
