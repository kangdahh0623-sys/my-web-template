# backend/app/main.py
# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import mealplan       # ✅ 하위 라우터 직접 임포트
# from app.api import analyze      # YOLO 라우터가 있으면 주석 해제

app = FastAPI(
    title=getattr(settings, "APP_NAME", "my-web-template backend"),
    version=getattr(settings, "APP_VERSION", "0.1.0"),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "FRONTEND_ORIGINS", ["http://localhost:3000","http://127.0.0.1:3000"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  집결 라우터 사용 금지. 하위 라우터를 직접 마운트
app.include_router(mealplan.router, prefix="/api/mealplan", tags=["mealplan"])
# app.include_router(analyze.router,  prefix="/api/analyze",  tags=["analyze"])

@app.get("/health")
def health():
    return {"status": "healthy"}
