# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

@app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

from app.api import analyze
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
print("✅ Analyze router 최우선 등록 완료")

@app.get("/test-direct")
async def test_direct():
    return {"message": "direct route working"}

@app.get("/api/analyze/health-direct")
async def analyze_health_direct():
    return {"status": "healthy", "service": "direct"}


# 라우터들 등록 (StaticFiles보다 먼저)
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

try:
    from app.api import csv_rpa
    app.include_router(csv_rpa.router, prefix="/api/csv-rpa", tags=["csv-rpa"])
    logger.info("CSV RPA router 등록 완료")
except ImportError as e:
    logger.warning(f"CSV RPA router 로드 실패: {e}")

try:
    from app.api import csv_llm
    app.include_router(csv_llm.router, prefix="/api/csv-llm", tags=["csv-llm"])
    logger.info("CSV LLM router 등록 완료")
except ImportError as e:
    logger.warning(f"CSV LLM router 로드 실패: {e}")

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

@app.get("/media/{path:path}")
async def serve_media(path: str):
    media_dir = getattr(settings, 'media_dir', 'media')
    file_path = os.path.join(media_dir, path)
    if os.path.exists(file_path):
        response = FileResponse(file_path)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        return response
    return {"error": "File not found"}

# media 디렉토리 마운트 (라우터들 이후에)
#media_dir = getattr(settings, 'media_dir', 'media')
#os.makedirs(media_dir, exist_ok=True)
#app.mount("/media", CORSStaticFiles(directory=media_dir), name="media")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=getattr(settings, "DEBUG", False)
    )