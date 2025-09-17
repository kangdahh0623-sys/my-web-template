# backend/app/services/workflow_agents.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import asyncio
from dataclasses import dataclass
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class WorkflowAlternative:
    id: int
    title: str
    description: str
    strategy_type: str
    estimated_cost: float
    target_calories: float
    features: List[str]
    highlight: str
    nutrition_score: Optional[float] = None
    economic_score: Optional[float] = None
    preference_score: Optional[float] = None
    feasibility_score: Optional[float] = None

@dataclass
class AgentAnalysis:
    nutrition_agent: float
    economic_agent: float
    student_agent: float
    operation_agent: float
    consensus: str
    recommendation: str

class RealDataAnalyzer:
    """실제 CSV 데이터 분석기"""
    
    def __init__(self):
        self.data_loaded = False
        self.nutrition_df = None
        self.price_df = None
        self.category_df = None
        self.student_pref_df = None
        self.pair_pref_df = None
        
    def load_data(self):
        """실제 CSV 데이터 로드"""
        try:
            base_path = Path(settings.resolve_path("backend/data"))
            
            self.nutrition_df = pd.read_csv(base_path / "meal_nutrition.csv")
            self.price_df = pd.read_csv(base_path / "meal_price.csv")
            self.category_df = pd.read_csv(base_path / "meal_category.csv")
            self.student_pref_df = pd.read_csv(base_path / "student_preference.csv")
            self.pair_pref_df = pd.read_csv(base_path / "pair_preference.csv")
            
            logger.info(f"데이터 로드 완료:")
            logger.info(f"- 영양소: {len(self.nutrition_df)}개 메뉴")
            logger.info(f"- 가격: {len(self.price_df)}개 메뉴")
            logger.info(f"- 카테고리: {len(self.category_df)}개 메뉴")
            logger.info(f"- 학생선호: {len(self.student_pref_df)}개 기록")
            logger.info(f"- 조합선호: {len(self.pair_pref_df)}개 조합")
            
            self.data_loaded = True
            
        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            raise
    
    def get_nutrition_stats(self):
        """영양소 통계 분석"""
        if not self.data_loaded:
            self.load_data()
            
        stats = {
            'avg_kcal': self.nutrition_df['kcal'].mean(),
            'avg_protein': self.nutrition_df['protein'].mean(),
            'avg_carbo': self.nutrition_df['carbo'].mean(),
            'avg_fat': self.nutrition_df['fat'].mean(),
            'high_protein_menus': len(self.nutrition_df[self.nutrition_df['protein'] > 20]),
            'low_fat_menus': len(self.nutrition_df[self.nutrition_df['fat'] < 10]),
            'vitamin_rich_menus': len(self.nutrition_df[self.nutrition_df['vitac'] > 20])
        }
        return stats
    
    def get_price_stats(self):
        """가격 통계 분석"""
        if not self.data_loaded:
            self.load_data()
            
        stats = {
            'avg_price': self.price_df['1인_가격'].mean(),
            'min_price': self.price_df['1인_가격'].min(),
            'max_price': self.price_df['1인_가격'].max(),
            'budget_friendly_menus': len(self.price_df[self.price_df['1인_가격'] < 3000]),
            'premium_menus': len(self.price_df[self.price_df['1인_가격'] > 5000])
        }
        return stats
    
    def get_student_preference_stats(self):
        """학생 선호도 통계 분석"""
        if not self.data_loaded:
            self.load_data()
            
        # 섭취율 기준 분석
        high_intake_dishes = self.student_pref_df[
            self.student_pref_df['Weighted_intake_ratio'] > 0.8
        ]['Dish'].unique()
        
        popular_dishes = self.student_pref_df.groupby('Dish').agg({
            'Mean_intake_cm3': 'mean',
            'Weighted_intake_ratio': 'mean',
            'Mean_kcal_intake': 'mean'
        }).sort_values('Weighted_intake_ratio', ascending=False)
        
        stats = {
            'high_intake_dishes': list(high_intake_dishes),
            'top_10_popular': popular_dishes.head(10).index.tolist(),
            'avg_intake_ratio': self.student_pref_df['Weighted_intake_ratio'].mean(),
            'total_dishes_analyzed': len(self.student_pref_df['Dish'].unique())
        }
        return stats

class NutritionistAgent:
    """영양사 에이전트 - 실제 영양 데이터 기반 분석"""
    
    def __init__(self, analyzer: RealDataAnalyzer):
        self.analyzer = analyzer
        self.expertise = "영양 균형 및 건강 관리"
    
    def analyze_strategy(self, strategy_type: str, params: Dict[str, Any]) -> float:
        """전략에 대한 영양사 관점 점수 계산"""
        try:
            nutrition_stats = self.analyzer.get_nutrition_stats()
            target_kcal = params.get('calories', 900)
            
            # 영양 균형 점수 계산
            protein_score = min(100, (nutrition_stats['avg_protein'] / 25) * 100)
            vitamin_score = (nutrition_stats['vitamin_rich_menus'] / len(self.analyzer.nutrition_df)) * 100
            calorie_match_score = max(0, 100 - abs(nutrition_stats['avg_kcal'] - target_kcal) / 10)
            
            # 전략별 가중치
            if strategy_type == 'nutrition':
                score = protein_score * 0.4 + vitamin_score * 0.4 + calorie_match_score * 0.2
            elif strategy_type == 'economic':
                score = protein_score * 0.3 + vitamin_score * 0.2 + calorie_match_score * 0.5
            else:  # preference
                score = protein_score * 0.2 + vitamin_score * 0.3 + calorie_match_score * 0.5
            
            logger.info(f"영양사 에이전트 분석: {strategy_type} 전략 -> {score:.1f}점")
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"영양사 에이전트 분석 실패: {e}")
            return 75.0  # 기본값

class EconomicAgent:
    """경제 에이전트 - 실제 가격 데이터 기반 분석"""
    
    def __init__(self, analyzer: RealDataAnalyzer):
        self.analyzer = analyzer
        self.expertise = "비용 효율성 및 예산 관리"
    
    def analyze_strategy(self, strategy_type: str, params: Dict[str, Any]) -> float:
        """전략에 대한 경제 관점 점수 계산"""
        try:
            price_stats = self.analyzer.get_price_stats()
            target_budget = params.get('budget', 5370)
            
            # 예산 준수 점수
            budget_score = max(0, 100 - abs(price_stats['avg_price'] - target_budget) / target_budget * 100)
            
            # 비용 효율성 점수
            efficiency_score = (price_stats['budget_friendly_menus'] / len(self.analyzer.price_df)) * 100
            
            # 가격 변동성 점수 (표준편차 기반)
            price_std = self.analyzer.price_df['1인_가격'].std()
            stability_score = max(0, 100 - (price_std / price_stats['avg_price']) * 100)
            
            # 전략별 가중치
            if strategy_type == 'economic':
                score = budget_score * 0.5 + efficiency_score * 0.3 + stability_score * 0.2
            elif strategy_type == 'nutrition':
                score = budget_score * 0.3 + efficiency_score * 0.5 + stability_score * 0.2
            else:  # preference
                score = budget_score * 0.4 + efficiency_score * 0.3 + stability_score * 0.3
            
            logger.info(f"경제 에이전트 분석: {strategy_type} 전략 -> {score:.1f}점")
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"경제 에이전트 분석 실패: {e}")
            return 70.0

class StudentAgent:
    """학생 에이전트 - 실제 선호도 데이터 기반 분석"""
    
    def __init__(self, analyzer: RealDataAnalyzer):
        self.analyzer = analyzer
        self.expertise = "학생 만족도 및 섭취율"
    
    def analyze_strategy(self, strategy_type: str, params: Dict[str, Any]) -> float:
        """전략에 대한 학생 관점 점수 계산"""
        try:
            pref_stats = self.analyzer.get_student_preference_stats()
            
            # 평균 섭취율 점수
            intake_score = pref_stats['avg_intake_ratio'] * 100
            
            # 인기 메뉴 비율 점수
            popular_ratio = len(pref_stats['top_10_popular']) / pref_stats['total_dishes_analyzed'] * 100
            
            # 메뉴 다양성 점수
            diversity_score = min(100, pref_stats['total_dishes_analyzed'] / 10 * 100)
            
            # 전략별 가중치
            if strategy_type == 'preference':
                score = intake_score * 0.5 + popular_ratio * 0.3 + diversity_score * 0.2
            elif strategy_type == 'nutrition':
                score = intake_score * 0.3 + popular_ratio * 0.2 + diversity_score * 0.5
            else:  # economic
                score = intake_score * 0.4 + popular_ratio * 0.4 + diversity_score * 0.2
            
            logger.info(f"학생 에이전트 분석: {strategy_type} 전략 -> {score:.1f}점")
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"학생 에이전트 분석 실패: {e}")
            return 65.0

class OperationAgent:
    """운영 에이전트 - 조리 효율성 및 운영 분석"""
    
    def __init__(self, analyzer: RealDataAnalyzer):
        self.analyzer = analyzer
        self.expertise = "조리 효율성 및 운영 관리"
    
    def analyze_strategy(self, strategy_type: str, params: Dict[str, Any]) -> float:
        """전략에 대한 운영 관점 점수 계산"""
        try:
            # 카테고리별 분포 분석
            category_distribution = self.analyzer.category_df['category'].value_counts()
            balance_score = (1 - category_distribution.std() / category_distribution.mean()) * 100
            
            # 조리 복잡도 추정 (카테고리 다양성 기반)
            complexity_score = max(0, 100 - len(category_distribution) * 5)
            
            # 대량 조리 적합성 (가격 안정성 기반)
            price_stability = 100 - (self.analyzer.price_df['1인_가격'].std() / 
                                   self.analyzer.price_df['1인_가격'].mean() * 100)
            
            # 전략별 가중치
            if strategy_type == 'economic':
                score = balance_score * 0.3 + complexity_score * 0.4 + price_stability * 0.3
            elif strategy_type == 'nutrition':
                score = balance_score * 0.4 + complexity_score * 0.3 + price_stability * 0.3
            else:  # preference
                score = balance_score * 0.2 + complexity_score * 0.5 + price_stability * 0.3
            
            logger.info(f"운영 에이전트 분석: {strategy_type} 전략 -> {score:.1f}점")
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"운영 에이전트 분석 실패: {e}")
            return 80.0

class MultiAgentCoordinator:
    """멀티 에이전트 조정자"""
    
    def __init__(self):
        self.analyzer = RealDataAnalyzer()
        self.nutritionist = NutritionistAgent(self.analyzer)
        self.economist = EconomicAgent(self.analyzer)
        self.student = StudentAgent(self.analyzer)
        self.operator = OperationAgent(self.analyzer)
    
    async def analyze_strategy_with_agents(self, strategy_id: int, params: Dict[str, Any]) -> AgentAnalysis:
        """멀티 에이전트 병렬 분석"""
        try:
            # 전략 타입 결정
            strategy_types = {1: 'nutrition', 2: 'economic', 3: 'preference'}
            strategy_type = strategy_types.get(strategy_id, 'nutrition')
            
            logger.info(f"멀티 에이전트 분석 시작: 전략 {strategy_id} ({strategy_type})")
            
            # 병렬 분석 실행
            tasks = [
                asyncio.create_task(asyncio.to_thread(self.nutritionist.analyze_strategy, strategy_type, params)),
                asyncio.create_task(asyncio.to_thread(self.economist.analyze_strategy, strategy_type, params)),
                asyncio.create_task(asyncio.to_thread(self.student.analyze_strategy, strategy_type, params)),
                asyncio.create_task(asyncio.to_thread(self.operator.analyze_strategy, strategy_type, params))
            ]
            
            scores = await asyncio.gather(*tasks)
            nutrition_score, economic_score, student_score, operation_score = scores
            
            # 합의 도출
            avg_score = sum(scores) / len(scores)
            consensus = self._generate_consensus(scores, strategy_type)
            recommendation = self._generate_recommendation(scores, strategy_type)
            
            logger.info(f"멀티 에이전트 분석 완료: 평균 {avg_score:.1f}점")
            
            return AgentAnalysis(
                nutrition_agent=nutrition_score,
                economic_agent=economic_score,
                student_agent=student_score,
                operation_agent=operation_score,
                consensus=consensus,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"멀티 에이전트 분석 실패: {e}")
            # 기본값 반환
            return AgentAnalysis(
                nutrition_agent=75.0,
                economic_agent=70.0,
                student_agent=65.0,
                operation_agent=80.0,
                consensus="분석 오류로 기본 평가 적용",
                recommendation="데이터 확인 후 재분석 권장"
            )
    
    def _generate_consensus(self, scores: List[float], strategy_type: str) -> str:
        """에이전트 합의 생성"""
        avg_score = sum(scores) / len(scores)
        max_score_idx = scores.index(max(scores))
        agent_names = ["영양사", "경제", "학생", "운영"]
        
        if avg_score >= 80:
            return f"모든 에이전트가 {strategy_type} 전략을 강력 추천 (평균 {avg_score:.1f}점)"
        elif avg_score >= 70:
            return f"{agent_names[max_score_idx]} 에이전트가 주도하여 {strategy_type} 전략 추천"
        else:
            return f"에이전트 간 의견 분분, {strategy_type} 전략 신중 검토 필요"
    
    def _generate_recommendation(self, scores: List[float], strategy_type: str) -> str:
        """추천 사항 생성"""
        nutrition_score, economic_score, student_score, operation_score = scores
        
        recommendations = []
        
        if nutrition_score >= 80:
            recommendations.append("영양 균형이 우수하여 건강한 성장 지원")
        if economic_score >= 80:
            recommendations.append("예산 효율성이 높아 지속 가능한 운영")
        if student_score >= 80:
            recommendations.append("학생 만족도가 높아 높은 섭취율 기대")
        if operation_score >= 80:
            recommendations.append("운영 효율성이 뛰어나 안정적 급식 제공")
        
        if not recommendations:
            recommendations.append("각 영역별 개선 방안 검토 필요")
        
        return " / ".join(recommendations)

# 전역 멀티 에이전트 조정자
multi_agent_coordinator = MultiAgentCoordinator()

# API에서 사용할 함수들
async def generate_strategies_from_request(user_request: str) -> List[WorkflowAlternative]:
    """실제 CSV 데이터 기반 전략 생성"""
    try:
        analyzer = RealDataAnalyzer()
        analyzer.load_data()
        
        # 실제 데이터 통계 수집
        nutrition_stats = analyzer.get_nutrition_stats()
        price_stats = analyzer.get_price_stats()
        pref_stats = analyzer.get_student_preference_stats()
        
        # 데이터 기반 전략 생성
        strategies = [
            WorkflowAlternative(
                id=1,
                title="영양 균형 중심 전략",
                description=f"실제 {len(analyzer.nutrition_df)}개 메뉴 데이터 분석 결과, 단백질 평균 {nutrition_stats['avg_protein']:.1f}g으로 성장기 학생에게 최적화",
                strategy_type="nutrition",
                estimated_cost=price_stats['avg_price'] * 1.1,
                target_calories=nutrition_stats['avg_kcal'],
                features=[
                    f"고단백 메뉴 {nutrition_stats['high_protein_menus']}개 포함",
                    f"비타민 풍부 메뉴 {nutrition_stats['vitamin_rich_menus']}개 확보",
                    f"평균 칼로리 {nutrition_stats['avg_kcal']:.0f}kcal 달성"
                ],
                highlight="실제 영양 데이터 기반 과학적 설계"
            ),
            WorkflowAlternative(
                id=2,
                title="경제성 우선 전략",
                description=f"실제 가격 데이터 분석으로 예산 친화적 메뉴 {price_stats['budget_friendly_menus']}개 활용하여 비용 효율성 극대화",
                strategy_type="economic",
                estimated_cost=price_stats['avg_price'] * 0.9,
                target_calories=nutrition_stats['avg_kcal'] * 0.95,
                features=[
                    f"예산 친화적 메뉴 {price_stats['budget_friendly_menus']}개 우선 선택",
                    f"평균 단가 {price_stats['avg_price']:.0f}원 기준 최적화",
                    f"가격 안정성 확보된 메뉴 중심 구성"
                ],
                highlight="실제 시장 가격 반영한 경제적 운영"
            ),
            WorkflowAlternative(
                id=3,
                title="선호도 중심 전략",
                description=f"실제 학생 {len(pref_stats['high_intake_dishes'])}개 고섭취 메뉴와 인기 상위 메뉴로 만족도 극대화",
                strategy_type="preference",
                estimated_cost=price_stats['avg_price'],
                target_calories=nutrition_stats['avg_kcal'] * 1.05,
                features=[
                    f"고섭취율 메뉴 {len(pref_stats['high_intake_dishes'])}개 중심 구성",
                    f"인기 상위 10개 메뉴 우선 배치",
                    f"평균 섭취율 {pref_stats['avg_intake_ratio']:.1%} 기준 선별"
                ],
                highlight="실제 학생 데이터 기반 높은 만족도"
            )
        ]
        
        logger.info(f"실제 CSV 데이터 기반 {len(strategies)}개 전략 생성 완료")
        return strategies
        
    except Exception as e:
        logger.error(f"전략 생성 실패: {e}")
        raise

async def analyze_strategy_with_agents(strategy_id: int, params: Dict[str, Any]) -> AgentAnalysis:
    """실제 멀티 에이전트 분석"""
    return await multi_agent_coordinator.analyze_strategy_with_agents(strategy_id, params)

async def parse_natural_language_params(natural_text: str, current_params: Dict[str, Any]) -> Dict[str, Any]:
    """확장된 자연어 파라미터 파싱"""
    try:
        result = current_params.copy()
        changes = []
        text = natural_text.lower()
        
        import re
        
        # 예산 관련 키워드: "예산", "가격", "원", "비용"
        budget_keywords = ["예산", "가격", "원", "비용", "돈"]
        if any(keyword in text for keyword in budget_keywords):
            numbers = re.findall(r'\d+', natural_text)
            if numbers:
                new_budget = int(numbers[0])
                if new_budget > 1000:
                    result['budget'] = new_budget
                    changes.append(f"예산을 {new_budget:,}원으로 변경")
        
        # 기간 관련 키워드: "일", "기간", "날"
        period_keywords = ["일", "기간", "날", "day"]
        if any(keyword in text for keyword in period_keywords):
            numbers = re.findall(r'\d+', natural_text)
            if numbers:
                new_days = int(numbers[-1])
                if 1 <= new_days <= 365:
                    result['days'] = new_days
                    changes.append(f"기간을 {new_days}일로 변경")
        
        # 칼로리 관련 키워드: "칼로리", "kcal", "열량"
        calorie_keywords = ["칼로리", "kcal", "열량"]
        if any(keyword in text for keyword in calorie_keywords):
            numbers = re.findall(r'\d+', natural_text)
            if numbers:
                new_calories = int(numbers[0])
                if 500 <= new_calories <= 2000:
                    result['calories'] = new_calories
                    changes.append(f"목표 칼로리를 {new_calories}kcal로 변경")
        
        # 단백질 관련 키워드: "단백질", "protein"
        if "단백질" in text or "protein" in text:
            numbers = re.findall(r'\d+', natural_text)
            if numbers:
                new_protein = int(numbers[0])
                if 10 <= new_protein <= 50:
                    result['protein'] = new_protein
                    changes.append(f"단백질 목표를 {new_protein}g으로 변경")
        
        # 비타민C 관련 키워드: "비타민c", "vitaminc", "비타민 c"
        if "비타민c" in text or "vitamin" in text:
            numbers = re.findall(r'\d+', natural_text)
            if numbers:
                new_vitaminc = int(numbers[0])
                if 20 <= new_vitaminc <= 200:
                    result['vitaminC'] = new_vitaminc
                    changes.append(f"비타민C 목표를 {new_vitaminc}mg으로 변경")
        
        # 칼슘 관련 키워드: "칼슘", "calcium"
        if "칼슘" in text or "calcium" in text:
            numbers = re.findall(r'\d+', natural_text)
            if numbers:
                new_calcium = int(numbers[0])
                if 100 <= new_calcium <= 1000:
                    result['calcium'] = new_calcium
                    changes.append(f"칼슘 목표를 {new_calcium}mg으로 변경")
        
        # 철분 관련 키워드: "철분", "iron"
        if "철분" in text or "iron" in text:
            numbers = re.findall(r'\d+', natural_text)
            if numbers:
                new_iron = int(numbers[0])
                if 3 <= new_iron <= 20:
                    result['iron'] = new_iron
                    changes.append(f"철분 목표를 {new_iron}mg으로 변경")
        
        # 영양소 비율 관련
        if "탄수화물" in text and "%" in text:
            numbers = re.findall(r'\d+', natural_text)
            if numbers:
                new_carb_ratio = int(numbers[0])
                if 40 <= new_carb_ratio <= 80:
                    result['carbRatio'] = new_carb_ratio
                    changes.append(f"탄수화물 비율을 {new_carb_ratio}%로 변경")
        
        if "단백질" in text and "%" in text:
            numbers = re.findall(r'\d+', natural_text)
            if numbers:
                new_protein_ratio = int(numbers[0])
                if 5 <= new_protein_ratio <= 30:
                    result['proteinRatio'] = new_protein_ratio
                    changes.append(f"단백질 비율을 {new_protein_ratio}%로 변경")
        
        if "지방" in text and "%" in text:
            numbers = re.findall(r'\d+', natural_text)
            if numbers:
                new_fat_ratio = int(numbers[0])
                if 10 <= new_fat_ratio <= 40:
                    result['fatRatio'] = new_fat_ratio
                    changes.append(f"지방 비율을 {new_fat_ratio}%로 변경")
        
        result['changes'] = changes
        logger.info(f"확장된 자연어 파싱 완료: {changes}")
        return result
        
    except Exception as e:
        logger.error(f"자연어 파싱 실패: {e}")
        current_params['changes'] = ["파싱 오류 발생"]
        return current_params