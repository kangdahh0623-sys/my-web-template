# backend/app/services/rpa_analyzer.py
import pandas as pd
import numpy as np
from typing import List, Dict

class MenuAnalysisRPA:
    def analyze_ga_results(self, results: List[Dict]) -> Dict:
        """3개 GA 결과를 자동으로 분석"""
        
        analysis = []
        
        for result in results:
            menu_data = pd.DataFrame(result['menuPlan'])
            
            # 자동 지표 계산
            metrics = {
                'cost_efficiency': self._calculate_cost_efficiency(menu_data),
                'nutrition_balance': self._calculate_nutrition_balance(menu_data),
                'menu_diversity': self._calculate_diversity(menu_data),
                'constraint_compliance': self._check_constraints(menu_data)
            }
            
            # 자동 장단점 도출
            pros, cons = self._generate_pros_cons(metrics)
            
            analysis.append({
                'metrics': metrics,
                'pros': pros,
                'cons': cons,
                'risk_score': self._calculate_risk_score(metrics)
            })
            
        return analysis
    
    def _calculate_cost_efficiency(self, df: pd.DataFrame) -> float:
        """비용 효율성 자동 계산"""
        daily_costs = df['day_cost'].values
        return 100 - (np.std(daily_costs) / np.mean(daily_costs) * 100)
    
    def _calculate_nutrition_balance(self, df: pd.DataFrame) -> float:
        """영양 균형 자동 계산"""
        calories = df['day_kcal'].values
        target = 900
        deviation = np.mean(np.abs(calories - target)) / target * 100
        return max(0, 100 - deviation)
    
    def _generate_pros_cons(self, metrics: Dict) -> tuple:
        """지표 기반 자동 장단점 생성"""
        pros = []
        cons = []
        
        if metrics['cost_efficiency'] > 80:
            pros.append("비용 효율성이 매우 우수함")
        elif metrics['cost_efficiency'] < 60:
            cons.append("비용 편차가 큰 편임")
            
        if metrics['nutrition_balance'] > 85:
            pros.append("영양 균형이 잘 맞춰져 있음")
        elif metrics['nutrition_balance'] < 70:
            cons.append("영양 균형 개선이 필요함")
            
        return pros, cons