import pandas as pd
import numpy as np
from typing import Dict, List, Any
import re
import json
from pathlib import Path

class CSVLLMAnalyzer:
    def __init__(self, data_paths: Dict[str, str]):
        self.nutrition_df = pd.read_csv(data_paths['nutrition'])
        self.price_df = pd.read_csv(data_paths['price'])
        self.category_df = pd.read_csv(data_paths.get('category', '')) if data_paths.get('category') else None
        
        # CSV 데이터 기반 지식베이스 구축
        self._build_knowledge_base()
    
    def _build_knowledge_base(self):
        """CSV 데이터로 지식베이스 구축"""
        # 가격대별 메뉴 분류
        self.price_ranges = {
            'low': self.price_df[self.price_df['1인_가격'] <= 1000]['menu'].tolist(),
            'medium': self.price_df[(self.price_df['1인_가격'] > 1000) & (self.price_df['1인_가격'] <= 2000)]['menu'].tolist(),
            'high': self.price_df[self.price_df['1인_가격'] > 2000]['menu'].tolist()
        }
        
        # 영양가별 메뉴 분류
        self.nutrition_ranges = {
            'high_protein': self.nutrition_df[self.nutrition_df['protein'] > 15]['menu'].tolist(),
            'high_kcal': self.nutrition_df[self.nutrition_df['kcal'] > 300]['menu'].tolist(),
            'low_kcal': self.nutrition_df[self.nutrition_df['kcal'] <= 200]['menu'].tolist()
        }
        
        # 전체 메뉴 통계
        self.menu_stats = {
            'total_menus': len(self.nutrition_df),
            'avg_price': self.price_df['1인_가격'].mean(),
            'avg_kcal': self.nutrition_df['kcal'].mean(),
            'price_range': (self.price_df['1인_가격'].min(), self.price_df['1인_가격'].max())
        }

    def analyze_user_request(self, user_request: str, current_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """사용자 요청을 CSV 데이터 기반으로 분석하여 3가지 전략 생성"""
        
        # 사용자 요청에서 핵심 요구사항 추출
        requirements = self._extract_requirements(user_request)
        
        # CSV 데이터 기반으로 3가지 전략 생성
        strategies = self._generate_strategies_from_data(requirements, current_params)
        
        return strategies
    
    def _extract_requirements(self, user_request: str) -> Dict[str, Any]:
        """사용자 요청에서 요구사항 추출"""
        requirements = {
            'budget_priority': False,
            'nutrition_priority': False,
            'preference_priority': False,
            'special_needs': []
        }
        
        # 키워드 기반 의도 분석
        request_lower = user_request.lower()
        
        if any(word in request_lower for word in ['절약', '경제적', '저렴', '비용', '예산']):
            requirements['budget_priority'] = True
            
        if any(word in request_lower for word in ['영양', '건강', '균형', '단백질', '비타민']):
            requirements['nutrition_priority'] = True
            
        if any(word in request_lower for word in ['맛있', '선호', '좋아', '인기', '만족']):
            requirements['preference_priority'] = True
            
        if any(word in request_lower for word in ['알레르기', '채식', '할랄']):
            requirements['special_needs'].append('식이제한')
            
        return requirements
    
    def _generate_strategies_from_data(self, requirements: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """CSV 데이터 기반 전략 생성"""
        
        strategies = []
        
        # 전략 1: 영양 균형 중심 (실제 영양 데이터 기반)
        nutrition_strategy = self._create_nutrition_strategy(params)
        strategies.append(nutrition_strategy)
        
        # 전략 2: 경제성 우선 (실제 가격 데이터 기반)
        economic_strategy = self._create_economic_strategy(params)
        strategies.append(economic_strategy)
        
        # 전략 3: 균형 접근 (데이터 종합 분석)
        balanced_strategy = self._create_balanced_strategy(params, requirements)
        strategies.append(balanced_strategy)
        
        return strategies
    
    def _create_nutrition_strategy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """실제 영양 데이터 기반 영양 전략"""
        
        # 고단백, 균형 영양 메뉴들 선별
        high_nutrition_menus = self.nutrition_df[
            (self.nutrition_df['protein'] > self.nutrition_df['protein'].mean()) &
            (self.nutrition_df['kcal'] > 200) &
            (self.nutrition_df['kcal'] < 400)
        ]
        
        estimated_cost = self._calculate_strategy_cost(high_nutrition_menus, params)
        
        return {
            'id': 1,
            'title': '실제 데이터 기반 영양 균형 전략',
            'description': f'CSV의 {len(high_nutrition_menus)}개 고영양 메뉴 활용으로 {params["calories"]}kcal 목표 달성',
            'strategy_type': 'nutrition',
            'estimated_cost': estimated_cost,
            'target_calories': int(params['calories'] * 1.02),
            'features': [
                f'평균 단백질 {high_nutrition_menus["protein"].mean():.1f}g 확보',
                f'{len(self.nutrition_ranges["high_protein"])}개 고단백 메뉴 활용',
                '실제 영양성분표 기반 설계'
            ],
            'highlight': f'CSV 영양 데이터 {len(self.nutrition_df)}개 메뉴 분석 결과',
            'data_basis': {
                'menu_count': len(high_nutrition_menus),
                'avg_protein': high_nutrition_menus['protein'].mean(),
                'avg_kcal': high_nutrition_menus['kcal'].mean()
            }
        }
    
    def _create_economic_strategy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """실제 가격 데이터 기반 경제 전략"""
        
        # 저가 메뉴들 선별
        budget_menus = self.price_df[self.price_df['1인_가격'] <= self.price_df['1인_가격'].quantile(0.3)]
        
        # 영양 데이터와 조인하여 영양가도 확인
        budget_with_nutrition = budget_menus.merge(self.nutrition_df, on='menu', how='inner')
        
        estimated_cost = int(params['budget'] * 0.85)
        
        return {
            'id': 2,
            'title': '실제 가격 데이터 기반 경제성 전략',
            'description': f'CSV의 {len(budget_menus)}개 저가 메뉴로 {params["days"]}일 운영비 절감',
            'strategy_type': 'economic',
            'estimated_cost': estimated_cost,
            'target_calories': int(params['calories'] * 0.95),
            'features': [
                f'평균 {budget_menus["1인_가격"].mean():.0f}원 메뉴 활용',
                f'{params["budget"] - estimated_cost}원 예산 절약',
                f'하위 30% 가격대 {len(budget_menus)}개 메뉴 선별'
            ],
            'highlight': f'실제 가격 데이터 {len(self.price_df)}개 메뉴 분석 기반',
            'data_basis': {
                'menu_count': len(budget_menus),
                'avg_price': budget_menus['1인_가격'].mean(),
                'price_range': (budget_menus['1인_가격'].min(), budget_menus['1인_가격'].max())
            }
        }
    
    def _create_balanced_strategy(self, params: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 종합 분석 기반 균형 전략"""
        
        # 가격과 영양의 균형점 찾기
        merged_data = self.price_df.merge(self.nutrition_df, on='menu', how='inner')
        merged_data['cost_per_kcal'] = merged_data['1인_가격'] / merged_data['kcal']
        merged_data['nutrition_score'] = (merged_data['protein'] * 4 + merged_data['kcal']) / merged_data['1인_가격']
        
        # 영양 대비 가격 효율이 좋은 메뉴들
        balanced_menus = merged_data[
            (merged_data['cost_per_kcal'] <= merged_data['cost_per_kcal'].median()) &
            (merged_data['nutrition_score'] >= merged_data['nutrition_score'].median())
        ]
        
        estimated_cost = self._calculate_strategy_cost(balanced_menus, params)
        
        return {
            'id': 3,
            'title': '데이터 최적화 기반 균형 전략',
            'description': f'가격 대비 영양가 분석으로 {len(balanced_menus)}개 최적 메뉴 선별',
            'strategy_type': 'balanced',
            'estimated_cost': estimated_cost,
            'target_calories': params['calories'],
            'features': [
                f'칼로리당 {balanced_menus["cost_per_kcal"].mean():.1f}원 효율',
                f'영양점수 상위 50% {len(balanced_menus)}개 메뉴',
                '가격-영양 최적화 알고리즘 적용'
            ],
            'highlight': f'CSV 데이터 {len(merged_data)}개 메뉴 종합 분석',
            'data_basis': {
                'menu_count': len(balanced_menus),
                'avg_cost_per_kcal': balanced_menus['cost_per_kcal'].mean(),
                'avg_nutrition_score': balanced_menus['nutrition_score'].mean()
            }
        }
    
    def _calculate_strategy_cost(self, menu_df: pd.DataFrame, params: Dict[str, Any]) -> int:
        """전략별 예상 비용 계산"""
        if 'kcal' in menu_df.columns and '1인_가격' in menu_df.columns:
            # 칼로리 목표 달성에 필요한 메뉴 조합 예상
            target_daily_kcal = params['calories']
            avg_menu_kcal = menu_df['kcal'].mean()
            menus_needed_per_day = target_daily_kcal / avg_menu_kcal
            
            avg_price = menu_df['1인_가격'].mean()
            daily_cost = avg_price * menus_needed_per_day
            
            return int(daily_cost)
        else:
            # 가격 데이터만 있는 경우
            return int(menu_df['1인_가격'].mean() * 5)  # 5개 메뉴 기준