# backend/main.py (또는 app/main.py)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
import os
import logging
from pathlib import Path

from app.core.config import settings
from app.api import analyze, mealplan

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="급식줍쇼 API",
    description="AI 기반 급식 관리 솔루션",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ===== CORS 미들웨어 설정 (가장 중요!) =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.allow_credentials,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
    max_age=settings.max_age,
)

# ===== 신뢰할 수 있는 호스트 설정 =====
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "*"]
)

# ===== 타임아웃 미들웨어 추가 =====
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        # 식단 최적화 요청은 더 긴 타임아웃
        if "/mealplan/optimize" in str(request.url):
            timeout = settings.optimization_timeout
        else:
            timeout = settings.request_timeout
            
        response = await asyncio.wait_for(
            call_next(request), 
            timeout=timeout
        )
        return response
    except asyncio.TimeoutError:
        logger.error(f"Request timeout: {request.url}")
        return JSONResponse(
            status_code=408,
            content={"detail": "Request timeout. Please try again."}
        )
    except Exception as e:
        logger.error(f"Middleware error: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# ===== 에러 핸들러 =====
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc} for {request.url}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# ===== 헬스 체크 엔드포인트 =====
@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.environment}

@app.get("/")
async def root():
    return {"message": "급식줍쇼 API 서버", "docs": "/docs"}

# ===== 라우터 등록 =====
app.include_router(analyze.router, prefix="/api")
app.include_router(mealplan.router)  # prefix는 이미 mealplan.py에서 "/api"로 설정됨

# ===== 정적 파일 서빙 (미디어 파일용) =====
media_dir = Path(settings.media_dir)
media_dir.mkdir(exist_ok=True)

app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

# ===== 서버 실행을 위한 설정 =====
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
        timeout_keep_alive=settings.keep_alive_timeout,
        timeout_graceful_shutdown=30,
        access_log=settings.debug,
        log_level="info" if settings.debug else "warning"
    )