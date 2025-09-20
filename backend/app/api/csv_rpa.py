from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.csv_rpa_analyzer import CSVRPAAnalyzer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class RPAAnalysisRequest(BaseModel):
    menu_results: List[Dict[str, Any]]
 
    
@router.post("/analyze-results")
async def analyze_with_csv_rpa(request: RPAAnalysisRequest):
    """CSV 데이터 기반 RPA 분석"""
    try:
        data_paths = {
            'nutrition': settings.resolve_path(settings.meal_nutrition_csv),
            'price': settings.resolve_path(settings.meal_price_csv),
            'student_pref': settings.resolve_path(settings.meal_student_pref_csv),
        }
        
        analyzer = CSVRPAAnalyzer(data_paths)
        analysis_results = analyzer.analyze_menu_results(request.menu_results)
        
        return {
            "status": "success",
            "analysis": analysis_results,
            "data_source": "실제 CSV 데이터 기반 분석"
        }
        
    except Exception as e:
        logger.error(f"CSV RPA 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"RPA 분석 중 오류: {str(e)}")