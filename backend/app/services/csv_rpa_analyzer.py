import pandas as pd
import numpy as np
from typing import Dict, List, Any
import os
from pathlib import Path

class CSVRPAAnalyzer:
    def __init__(self, data_paths: Dict[str, str]):
        self.nutrition_df = pd.read_csv(data_paths['nutrition'])
        self.price_df = pd.read_csv(data_paths['price']) 
        self.preference_df = pd.read_csv(data_paths.get('student_pref', '')) if data_paths.get('student_pref') else None
        
    def analyze_menu_results(self, menu_results: List[Dict]) -> List[Dict]:
        """3개 GA 결과를 실제 CSV 데이터로 분석"""
        
        analyses = []
        
        for result in menu_results:
            menu_plan = result['menuPlan']
            strategy_type = result['alternative']['strategy_type']
            
            # 실제 데이터 기반 지표 계산
            nutrition_score = self._calculate_nutrition_score(menu_plan)
            economic_score = self._calculate_economic_score(menu_plan)
            preference_score = self._calculate_preference_score(menu_plan)
            feasibility_score = self._calculate_feasibility_score(menu_plan)
            
            # 데이터 기반 장단점 생성
            pros, cons, risks = self._generate_analysis_from_data(
                nutrition_score, economic_score, preference_score, strategy_type
            )
            
            analyses.append({
                'strategy_type': strategy_type,
                'scores': {
                    'nutrition': nutrition_score,
                    'economic': economic_score, 
                    'preference': preference_score,
                    'feasibility': feasibility_score
                },
                'pros': pros,
                'cons': cons,
                'risks': risks,
                'data_insights': self._get_data_insights(menu_plan)
            })
            
        return analyses
    
    def _calculate_nutrition_score(self, menu_plan: List[Dict]) -> float:
        """실제 영양 데이터로 균형도 계산"""
        total_score = 0
        day_count = 0
        
        for day in menu_plan:
            day_nutrition = []
            for menu_type in ['rice', 'soup', 'side1', 'side2', 'side3']:
                menu_name = day.get(menu_type, '')
                nutrition_data = self.nutrition_df[self.nutrition_df['menu'] == menu_name]
                if not nutrition_data.empty:
                    day_nutrition.append(nutrition_data.iloc[0])
            
            if day_nutrition:
                # 일일 영양 균형도 계산
                daily_kcal = sum([n.get('kcal', 0) for n in day_nutrition])
                daily_protein = sum([n.get('protein', 0) for n in day_nutrition])
                
                # 목표 대비 점수 (900kcal, 단백질 비율 등)
                kcal_score = min(100, (daily_kcal / 900) * 100) if daily_kcal > 0 else 0
                protein_score = min(100, (daily_protein / 30) * 100) if daily_protein > 0 else 0
                
                total_score += (kcal_score + protein_score) / 2
                day_count += 1
        
        return total_score / day_count if day_count > 0 else 0
    
    def _calculate_economic_score(self, menu_plan: List[Dict]) -> float:
        """실제 가격 데이터로 경제성 계산"""
        total_cost = 0
        day_count = 0
        
        for day in menu_plan:
            day_cost = 0
            for menu_type in ['rice', 'soup', 'side1', 'side2', 'side3']:
                menu_name = day.get(menu_type, '')
                price_data = self.price_df[self.price_df['menu'] == menu_name]
                if not price_data.empty:
                    day_cost += price_data.iloc[0].get('1인_가격', 0)
            
            total_cost += day_cost
            day_count += 1
        
        avg_daily_cost = total_cost / day_count if day_count > 0 else 0
        
        # 목표 예산(5370원) 대비 점수
        budget_efficiency = min(100, (5370 / avg_daily_cost) * 100) if avg_daily_cost > 0 else 0
        return budget_efficiency
    
    def _calculate_preference_score(self, menu_plan: List[Dict]) -> float:
        """학생 선호도 데이터로 만족도 계산"""
        if self.preference_df is None:
            return 75.0  # 기본값
        
        preference_scores = []
        
        for day in menu_plan:
            for menu_type in ['rice', 'soup', 'side1', 'side2', 'side3']:
                menu_name = day.get(menu_type, '')
                pref_data = self.preference_df[self.preference_df['Dish'] == menu_name]
                if not pref_data.empty:
                    score = pref_data.iloc[0].get('Weighted_intake_ratio', 0.5) * 100
                    preference_scores.append(score)
        
        return np.mean(preference_scores) if preference_scores else 50.0
    
    def _calculate_feasibility_score(self, menu_plan: List[Dict]) -> float:
        """실행 가능성 점수 계산"""
        # 메뉴 다양성, 반복도 등 계산
        all_menus = []
        for day in menu_plan:
            for menu_type in ['rice', 'soup', 'side1', 'side2', 'side3']:
                menu_name = day.get(menu_type, '')
                if menu_name:
                    all_menus.append(menu_name)
        
        unique_ratio = len(set(all_menus)) / len(all_menus) if all_menus else 0
        return unique_ratio * 100
    
    def _generate_analysis_from_data(self, nutrition_score: float, economic_score: float, 
                                   preference_score: float, strategy_type: str) -> tuple:
        """데이터 기반 장단점 생성"""
        
        pros = []
        cons = []
        risks = []
        
        # 영양 점수 기반 분석
        if nutrition_score > 80:
            pros.append(f"영양 균형도 {nutrition_score:.1f}점으로 우수함")
        elif nutrition_score < 60:
            cons.append(f"영양 균형도 {nutrition_score:.1f}점으로 개선 필요")
        
        # 경제성 점수 기반 분석  
        if economic_score > 85:
            pros.append(f"예산 효율성 {economic_score:.1f}점으로 매우 우수")
        elif economic_score < 70:
            cons.append(f"예산 효율성 {economic_score:.1f}점으로 비용 부담")
            
        # 선호도 점수 기반 분석
        if preference_score > 75:
            pros.append(f"학생 선호도 {preference_score:.1f}점으로 높은 만족도 예상")
        elif preference_score < 60:
            cons.append(f"학생 선호도 {preference_score:.1f}점으로 섭취율 우려")
        
        # 전략별 특화 분석
        if strategy_type == 'nutrition':
            if nutrition_score < economic_score:
                risks.append("영양 중심 전략이지만 경제성이 더 높아 전략 재검토 필요")
        elif strategy_type == 'economic':
            if economic_score < 80:
                risks.append("경제성 전략이지만 비용 절감 효과가 제한적")
        elif strategy_type == 'preference':
            if preference_score < 70:
                risks.append("선호도 중심이지만 학생 만족도가 기대에 못 미침")
        
        return pros, cons, risks
    
    def _get_data_insights(self, menu_plan: List[Dict]) -> Dict[str, Any]:
        """추가 데이터 인사이트"""
        menu_frequency = {}
        for day in menu_plan:
            for menu_type in ['rice', 'soup', 'side1', 'side2', 'side3']:
                menu_name = day.get(menu_type, '')
                if menu_name:
                    menu_frequency[menu_name] = menu_frequency.get(menu_name, 0) + 1
        
        most_frequent = max(menu_frequency.items(), key=lambda x: x[1]) if menu_frequency else ("없음", 0)
        
        return {
            'most_frequent_menu': most_frequent[0],
            'repetition_count': most_frequent[1],
            'unique_menu_count': len(menu_frequency),
            'menu_diversity_ratio': len(menu_frequency) / sum(menu_frequency.values()) if menu_frequency else 0
        }