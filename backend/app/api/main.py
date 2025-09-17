# backend/main.py (업데이트된 버전)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import os

# 기존 라우터들
from app.api.main import router as main_router
from app.api.analyze import router as analyze_router  
from app.api.mealplan import router as mealplan_router
from app.api.admin import router as admin_router
from app.api.webhook import router as webhook_router

# 새로 추가된 라우터들
from app.api.strategy import router as strategy_router
from app.api.nlp import router as nlp_router
from app.api.report import router as report_router

from app.core.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="급식줍쇼 - 급식 메뉴 최적화 시스템",
    description="AI 기반 학교급식 메뉴 최적화 및 영양 분석 시스템",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포시에는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (미디어 파일 등)
media_dir = getattr(settings, 'MEDIA_DIR', 'media')
if os.path.exists(media_dir):
    app.mount("/media", StaticFiles(directory=media_dir), name="media")
    logger.info(f"정적 파일 서빙 설정: {media_dir}")

# 기존 라우터 등록
app.include_router(main_router, prefix="/api", tags=["메인"])
app.include_router(analyze_router, prefix="/api/analyze", tags=["식단 분석"])
app.include_router(mealplan_router, prefix="/api/mealplan", tags=["식단 최적화"])
app.include_router(admin_router, prefix="/api/admin", tags=["관리자"])
app.include_router(webhook_router, prefix="/api/webhook", tags=["웹훅"])

# 새로운 라우터 등록 🚀
app.include_router(strategy_router, prefix="/api/strategy", tags=["전략 생성"])
app.include_router(nlp_router, prefix="/api/nlp", tags=["자연어 처리"])
app.include_router(report_router, prefix="/api/report", tags=["보고서 생성"])

# 글로벌 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"글로벌 예외 발생: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "서버 내부 오류가 발생했습니다.",
            "detail": str(exc) if settings.DEBUG else "Internal Server Error"
        }
    )

# 애플리케이션 시작/종료 이벤트
@app.on_event("startup")
async def startup_event():
    logger.info("=== 급식줍쇼 시스템 시작 ===")
    logger.info("🍽️ 급식 메뉴 최적화 시스템 v2.0.0")
    logger.info("📊 새로운 기능:")
    logger.info("  • LLM 기반 메뉴 전략 생성")
    logger.info("  • 자연어 파라미터 변경")
    logger.info("  • 가정통신문 생성 (PDF/워드)")
    logger.info("  • 4단계 워크플로우 지원")
    logger.info("==============================")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("급식줍쇼 시스템 종료")

# 루트 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "🍽️ 급식줍쇼 - 급식 메뉴 최적화 시스템",
        "version": "2.0.0",
        "description": "AI 기반 학교급식 메뉴 최적화 및 영양 분석 시스템",
        "features": [
            "LLM 기반 메뉴 전략 생성",
            "자연어 파라미터 조정", 
            "GA 메뉴 최적화",
            "영양소 분석",
            "가정통신문 생성"
        ],
        "workflow": [
            "1단계: 사용자 요청 입력",
            "2단계: AI 전략 대안 생성",
            "3단계: 설정 조정 및 선택",
            "4단계: 메뉴 최적화 실행"
        ],
        "api_docs": "/docs",
        "health_check": "/health"
    }

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """시스템 상태 확인"""
    try:
        # 각 서비스 상태 확인
        from app.services.llm_strategy import llm_strategy_service
        from app.services.natural_language import nl_processor
        from app.services.report_generator import report_generator, REPORTLAB_AVAILABLE, DOCX_AVAILABLE
        
        return {
            "status": "healthy",
            "timestamp": "2024-12-19",
            "services": {
                "llm_strategy": "available",
                "natural_language": "available", 
                "report_generator": "available",
                "ga_optimizer": "available",
                "intake_analyzer": "available"
            },
            "capabilities": {
                "pdf_generation": REPORTLAB_AVAILABLE,
                "docx_generation": DOCX_AVAILABLE,
                "korean_font": report_generator.font_setup_done
            }
        }
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )