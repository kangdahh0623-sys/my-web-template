# backend/app/api/report.py
"""
급식 보고서 생성 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import pandas as pd
import logging
from io import BytesIO

from app.services.report_generator import report_generator
from app.models.schemas import BaseResponse

logger = logging.getLogger(__name__)
router = APIRouter()

class SchoolInfo(BaseModel):
    """학교 정보"""
    name: str = Field(..., description="학교명")
    phone: Optional[str] = Field(None, description="연락처")
    address: Optional[str] = Field(None, description="주소")
    principal: Optional[str] = Field(None, description="교장명")
    nutritionist: Optional[str] = Field(None, description="영양사명")

class ReportRequest(BaseModel):
    """보고서 생성 요청"""
    menu_plan: List[Dict[str, Any]] = Field(..., description="메뉴 계획 데이터")
    summary: Dict[str, Any] = Field(..., description="요약 정보")
    school_info: Optional[SchoolInfo] = Field(None, description="학교 정보")
    format_type: str = Field("pdf", regex="^(pdf|docx)$", description="파일 형식")
    title: Optional[str] = Field(None, description="보고서 제목")

@router.post("/generate")
async def generate_report(request: ReportRequest):
    """
    급식 계획 보고서 생성 (PDF 또는 워드)
    
    Returns:
        StreamingResponse: 생성된 문서 파일
    """
    try:
        logger.info(f"보고서 생성 요청 - 형식: {request.format_type}")
        
        # DataFrame 변환
        menu_df = pd.DataFrame(request.menu_plan)
        
        # 학교 정보 딕셔너리 변환
        school_info_dict = None
        if request.school_info:
            school_info_dict = request.school_info.dict()
        
        # 보고서 생성
        document_bytes = report_generator.generate_school_report(
            menu_plan=menu_df,
            summary=request.summary,
            school_info=school_info_dict,
            format_type=request.format_type
        )
        
        # 파일명 생성
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        school_name = school_info_dict.get('name', '학교') if school_info_dict else '학교'
        
        if request.format_type == "pdf":
            filename = f"{school_name}_급식계획서_{timestamp}.pdf"
            media_type = "application/pdf"
        else:
            filename = f"{school_name}_급식계획서_{timestamp}.docx"
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        # 스트리밍 응답 반환
        return StreamingResponse(
            BytesIO(document_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"보고서 생성 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"보고서 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/preview")
async def preview_report(request: ReportRequest):
    """
    보고서 미리보기 데이터 생성
    
    Returns:
        보고서에 포함될 내용의 미리보기
    """
    try:
        logger.info("보고서 미리보기 생성")
        
        # 메뉴 데이터 처리
        menu_df = pd.DataFrame(request.menu_plan)
        
        # 합계 행 제외하고 실제 메뉴만
        menu_data = menu_df[menu_df['day'] != '합계'].copy() if 'day' in menu_df.columns else menu_df
        
        # 기본 정보 생성
        from datetime import datetime, timedelta
        today = datetime.now()
        period_start = today + timedelta(days=7)
        period_end = period_start + timedelta(days=request.summary.get('days', 20))
        
        school_name = request.school_info.name if request.school_info else '○○학교'
        
        preview_data = {
            "title": f"{school_name} 급식 계획서",
            "issue_date": today.strftime("%Y년 %m월 %d일"),
            "period": f"{period_start.strftime('%Y년 %m월 %d일')} ~ {period_end.strftime('%Y년 %m월 %d일')}",
            "total_days": request.summary.get('days', 20),
            "budget_per_person": request.summary.get('budget_won', 5370),
            "avg_calories": request.summary.get('avg_kcal', 900),
            "total_cost": request.summary.get('total_cost', 0),
            "nutrition_status": '우수' if request.summary.get('feasible', True) else '조정 필요',
            "menu_count": len(menu_data),
            "school_info": {
                "name": school_name,
                "phone": request.school_info.phone if request.school_info else "000-0000-0000",
                "nutritionist": request.school_info.nutritionist if request.school_info else "영양사"
            },
            "sample_menus": menu_data.head(7).to_dict('records') if not menu_data.empty else [],
            "notices": [
                "급식비는 매월 25일에 자동이체됩니다.",
                "식단은 식재료 수급 상황에 따라 변경될 수 있습니다.",
                "알레르기 유발 식품이 포함된 경우 별도 안내드립니다.",
                f"급식 관련 문의: 영양실 ({request.school_info.phone if request.school_info else '000-0000-0000'})"
            ]
        }
        
        return {
            "success": True,
            "message": "미리보기 생성 완료",
            "preview": preview_data
        }
        
    except Exception as e:
        logger.error(f"미리보기 생성 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"미리보기 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/templates")
async def get_report_templates():
    """사용 가능한 보고서 템플릿 목록"""
    return {
        "templates": [
            {
                "id": "standard",
                "name": "표준 가정통신문",
                "description": "일반적인 학교 급식 가정통신문 양식",
                "format": ["pdf", "docx"],
                "sections": [
                    "학교 정보",
                    "급식 기간 및 예산",
                    "영양 성분 요약",
                    "주간 메뉴표",
                    "학부모 안내사항"
                ]
            },
            {
                "id": "detailed",
                "name": "상세 영양 분석서",
                "description": "영양 성분별 상세 분석이 포함된 보고서",
                "format": ["pdf", "docx"],
                "sections": [
                    "학교 정보",
                    "급식 기간 및 예산", 
                    "상세 영양 분석",
                    "일별 칼로리 차트",
                    "주간 메뉴표",
                    "영양소별 권장량 비교",
                    "학부모 안내사항"
                ]
            }
        ],
        "supported_formats": ["pdf", "docx"],
        "requirements": {
            "pdf": "ReportLab 라이브러리 필요",
            "docx": "python-docx 라이브러리 필요"
        }
    }

@router.get("/status")
async def report_status():
    """보고서 생성 서비스 상태 확인"""
    try:
        from app.services.report_generator import REPORTLAB_AVAILABLE, DOCX_AVAILABLE
        
        return {
            "status": "healthy",
            "pdf_available": REPORTLAB_AVAILABLE,
            "docx_available": DOCX_AVAILABLE,
            "supported_formats": [
                format_type for format_type, available in 
                [("pdf", REPORTLAB_AVAILABLE), ("docx", DOCX_AVAILABLE)] 
                if available
            ]
        }
        
    except Exception as e:
        logger.error(f"상태 확인 실패: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/")
async def report_root():
    """보고서 API 루트"""
    return {
        "message": "Report Generation API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "POST /generate - 보고서 생성 및 다운로드",
            "preview": "POST /preview - 보고서 미리보기",
            "templates": "GET /templates - 템플릿 목록",
            "status": "GET /status - 서비스 상태"
        }
    }