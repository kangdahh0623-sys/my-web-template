# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  
import logging
import os

from app.core.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title=getattr(settings, "APP_NAME", "School Meal Optimizer"),
    version="1.0.0",
    description="웹 서비스 템플릿"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# media 디렉토리 보장 + 마운트
media_dir = getattr(settings, 'media_dir', 'media')
os.makedirs(media_dir, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_dir), name="media")

# API 라우터 등록 - 안전하게 import
try:
    from app.api.main import router as main_api_router
    app.include_router(main_api_router, prefix="/api")
    logger.info("Main API router 등록 완료")
except ImportError as e:
    logger.warning(f"Main API router 로드 실패: {e}")

try:
    from app.api import mealplan
    app.include_router(mealplan.router, prefix="/api/mealplan", tags=["mealplan"])
    logger.info("Mealplan router 등록 완료")
except ImportError as e:
    logger.warning(f"Mealplan router 로드 실패: {e}")

try:
    from app.api import admin
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    logger.info("Admin router 등록 완료")
except ImportError as e:
    logger.warning(f"Admin router 로드 실패: {e}")

try:
    from app.api import webhook
    app.include_router(webhook.router, prefix="/api/webhook", tags=["webhook"])
    logger.info("Webhook router 등록 완료")
except ImportError as e:
    logger.warning(f"Webhook router 로드 실패: {e}")

try:
    from app.api import workflow
    app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])
    logger.info("Workflow router 등록 완료")
except ImportError as e:
    logger.warning(f"Workflow router 로드 실패: {e}")


# 기본 라우트
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {getattr(settings, 'APP_NAME', 'School Meal Optimizer')}",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=getattr(settings, "DEBUG", False)
    )