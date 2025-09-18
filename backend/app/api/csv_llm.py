from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.csv_llm_analyzer import CSVLLMAnalyzer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class LLMAnalysisRequest(BaseModel):
    user_request: str
    current_params: Dict[str, Any]

@router.post("/analyze-request")
async def analyze_with_csv_llm(request: LLMAnalysisRequest):
    """CSV 데이터 기반 사용자 요청 분석"""
    try:
        data_paths = {
            'nutrition': settings.resolve_path(settings.meal_nutrition_csv),
            'price': settings.resolve_path(settings.meal_price_csv),
            'category': settings.resolve_path(settings.meal_category_csv) if hasattr(settings, 'meal_category_csv') else None,
        }
        
        analyzer = CSVLLMAnalyzer(data_paths)
        strategies = analyzer.analyze_user_request(request.user_request, request.current_params)
        
        return {
            "status": "success",
            "alternatives": strategies,
            "analysis_method": "CSV 데이터 기반 지능형 분석",
            "data_source": f"영양 데이터 {len(analyzer.nutrition_df)}개, 가격 데이터 {len(analyzer.price_df)}개 메뉴"
        }
        
    except Exception as e:
        logger.error(f"CSV LLM 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"LLM 분석 중 오류: {str(e)}")

@router.post("/parse-natural-language")
async def parse_with_csv_llm(request: LLMAnalysisRequest):
    """CSV 데이터 기반 자연어 파라미터 파싱"""
    try:
        data_paths = {
            'nutrition': settings.resolve_path(settings.meal_nutrition_csv),
            'price': settings.resolve_path(settings.meal_price_csv),
        }
        
        analyzer = CSVLLMAnalyzer(data_paths)
        
        # 기본 정규식 파싱
        user_text = request.user_request
        budgetMatch = re.search(r'(\d+)\s*원', user_text)
        daysMatch = re.search(r'(\d+)\s*일', user_text)
        caloriesMatch = re.search(r'(\d+)\s*(?:칼로리|kcal)', user_text, re.IGNORECASE)
        
        result = dict(request.current_params)
        changes = []
        
        # CSV 데이터 기반 검증 및 추천
        if budgetMatch:
            new_budget = int(budgetMatch.group(1))
            if new_budget < analyzer.menu_stats['avg_price'] * 3:
                changes.append(f"⚠️ 예산 {new_budget}원은 평균 메뉴 가격({analyzer.menu_stats['avg_price']:.0f}원) 대비 낮음")
            result['budget'] = new_budget
            changes.append(f"예산을 {new_budget}원으로 변경")
        
        if daysMatch:
            result['days'] = int(daysMatch.group(1))
            changes.append(f"기간을 {daysMatch.group(1)}일로 변경")
            
        if caloriesMatch:
            new_calories = int(caloriesMatch.group(1))
            if new_calories > analyzer.menu_stats['avg_kcal'] * 5:
                changes.append(f"⚠️ 목표 칼로리 {new_calories}는 일반적인 급식 칼로리를 초과")
            result['calories'] = new_calories
            changes.append(f"목표 칼로리를 {new_calories}로 변경")
        
        # CSV 기반 추가 인사이트
        changes.append(f"💡 현재 데이터베이스: {analyzer.menu_stats['total_menus']}개 메뉴, 평균 가격 {analyzer.menu_stats['avg_price']:.0f}원")
        
        result['changes'] = changes
        
        return result
        
    except Exception as e:
        logger.error(f"CSV 자연어 파싱 실패: {e}")
        raise HTTPException(status_code=500, detail=f"자연어 파싱 중 오류: {str(e)}")