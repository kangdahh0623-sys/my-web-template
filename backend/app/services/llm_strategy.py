# backend/app/services/llm_strategy.py
"""
LLM 기반 급식 메뉴 전략 대안 생성 서비스
사용자 요청을 분석하여 5가지 최적화 전략을 제시
"""

import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import openai  # 또는 다른 LLM 라이브러리
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class MenuAlternative:
    """메뉴 전략 대안 데이터 구조"""
    id: int
    title: str
    description: str
    estimated_cost: float
    target_calories: float
    features: List[str]
    pros: List[str]
    cons: List[str]
    risks: List[str]
    strategy_params: Dict[str, Any]

class LLMStrategyService:
    """LLM 전략 생성 서비스"""
    
    def __init__(self):
        # OpenAI API 키 설정 (환경변수에서)
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if self.api_key:
            openai.api_key = self.api_key
        logger.info("LLMStrategyService 초기화")

    def analyze_user_request(self, user_input: str) -> Dict[str, Any]:
        """사용자 요청 분석"""
        try:
            # 기본값
            extracted = {
                "days": 20,
                "budget": 5370,
                "target_calories": 900,
                "priority": "balanced",  # balanced, cost, nutrition, taste
                "special_requirements": []
            }
            
            # 간단한 키워드 추출 (실제로는 LLM 사용)
            text = user_input.lower()
            
            # 일수 추출
            import re
            days_match = re.search(r'(\d+)일', text)
            if days_match:
                extracted["days"] = int(days_match.group(1))
            
            # 예산 추출
            budget_match = re.search(r'(\d+)원', text)
            if budget_match:
                extracted["budget"] = int(budget_match.group(1))
            
            # 칼로리 추출
            cal_match = re.search(r'(\d+)kcal|(\d+)칼로리', text)
            if cal_match:
                cal_value = cal_match.group(1) or cal_match.group(2)
                extracted["target_calories"] = int(cal_value)
            
            # 우선순위 키워드 분석
            if any(word in text for word in ['영양', '건강', '균형']):
                extracted["priority"] = "nutrition"
            elif any(word in text for word in ['경제', '절약', '저렴', '예산']):
                extracted["priority"] = "cost"
            elif any(word in text for word in ['맛', '선호', '기호']):
                extracted["priority"] = "taste"
            
            # 특수 요구사항
            if '알레르기' in text:
                extracted["special_requirements"].append("allergy_free")
            if '채식' in text:
                extracted["special_requirements"].append("vegetarian")
            if '저염' in text:
                extracted["special_requirements"].append("low_sodium")
                
            logger.info(f"사용자 요청 분석 결과: {extracted}")
            return extracted
            
        except Exception as e:
            logger.error(f"사용자 요청 분석 실패: {e}")
            return {
                "days": 20, "budget": 5370, "target_calories": 900,
                "priority": "balanced", "special_requirements": []
            }

    def generate_alternatives_with_llm(self, user_request: str) -> List[MenuAlternative]:
        """LLM을 사용한 대안 생성 (실제 구현)"""
        try:
            analyzed = self.analyze_user_request(user_request)
            
            system_prompt = """
당신은 학교급식 전문 영양사입니다. 
사용자의 요청을 분석하여 5가지 서로 다른 급식 메뉴 전략을 제시해주세요.
각 전략은 다음 형식으로 작성해주세요:

1. 전략명
2. 간단한 설명 (1-2문장)
3. 예상 1인당 비용 (원)
4. 목표 칼로리
5. 주요 특징 3가지
6. 장점 3가지
7. 단점 2-3가지
8. 위험요소 2가지

전략은 다음과 같이 다양하게 구성해주세요:
- 영양 균형 중심
- 경제성 중심  
- 학생 선호도 중심
- 계절 식재료 중심
- 창의적/국제적 접근
"""

            user_prompt = f"""
사용자 요청: "{user_request}"

분석된 조건:
- 기간: {analyzed['days']}일
- 예산: {analyzed['budget']}원
- 목표 칼로리: {analyzed['target_calories']}kcal
- 우선순위: {analyzed['priority']}
- 특수요구: {', '.join(analyzed['special_requirements']) if analyzed['special_requirements'] else '없음'}

위 조건에 맞는 5가지 급식 메뉴 전략을 JSON 형태로 제시해주세요.
"""

            if self.api_key:
                # 실제 OpenAI API 호출
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                llm_response = response.choices[0].message.content
                # JSON 파싱 및 MenuAlternative 객체 생성
                return self._parse_llm_response(llm_response, analyzed)
            else:
                # API 키가 없으면 Mock 데이터 반환
                logger.warning("OpenAI API 키가 없어 Mock 데이터를 반환합니다.")
                return self._generate_mock_alternatives(analyzed)
                
        except Exception as e:
            logger.error(f"LLM 대안 생성 실패: {e}")
            return self._generate_mock_alternatives(self.analyze_user_request(user_request))

    def _parse_llm_response(self, llm_response: str, analyzed: Dict) -> List[MenuAlternative]:
        """LLM 응답을 파싱하여 MenuAlternative 객체로 변환"""
        try:
            # JSON 추출 시도
            alternatives = []
            
            # 실제 구현에서는 더 정교한 JSON 파싱 필요
            # 여기서는 Mock 데이터로 대체
            return self._generate_mock_alternatives(analyzed)
            
        except Exception as e:
            logger.error(f"LLM 응답 파싱 실패: {e}")
            return self._generate_mock_alternatives(analyzed)

    def _generate_mock_alternatives(self, analyzed: Dict) -> List[MenuAlternative]:
        """Mock 대안 데이터 생성"""
        base_budget = analyzed["budget"]
        base_calories = analyzed["target_calories"]
        
        alternatives = [
            MenuAlternative(
                id=1,
                title="영양 균형 중심 전략",
                description="단백질, 비타민, 무기질의 완벽한 균형을 맞춘 성장기 학생 맞춤 식단",
                estimated_cost=base_budget * 1.1,
                target_calories=base_calories * 1.05,
                features=["고단백 식품 강화", "비타민 A,C 풍부", "칼슘/철분 최적화"],
                pros=["영양소 완전 균형", "성장 발육 촉진", "면역력 강화", "학습능력 향상"],
                cons=["식재료 비용 상승", "조리 복잡도 증가", "일부 메뉴 기호도 우려"],
                risks=["예산 초과 위험", "식재료 수급 불안정"],
                strategy_params={
                    "protein_ratio": 1.2, "vitamin_focus": True, "mineral_enhanced": True,
                    "budget_flexibility": 0.1, "complexity_level": "high"
                }
            ),
            MenuAlternative(
                id=2,
                title="경제성 우선 전략",
                description="한정된 예산 내에서 최대한 다양하고 풍성한 메뉴를 제공하는 실용적 접근",
                estimated_cost=base_budget * 0.9,
                target_calories=base_calories * 0.95,
                features=["대용량 조리 최적화", "계절 할인 식재료 활용", "잔반 최소화 설계"],
                pros=["예산 절약 효과", "메뉴 다양성 확보", "안정적 운영", "학교 재정 부담 경감"],
                cons=["프리미엄 식재료 제한", "영양밀도 다소 부족", "창의적 메뉴 제약"],
                risks=["영양 불균형 우려", "품질 저하 가능성"],
                strategy_params={
                    "cost_optimization": True, "bulk_cooking": True, "seasonal_focus": True,
                    "budget_target": 0.9, "variety_priority": True
                }
            ),
            MenuAlternative(
                id=3,
                title="학생 선호도 중심 전략",
                description="학생 기호도 조사 결과를 바탕으로 한 높은 만족도와 섭취율을 목표로 하는 식단",
                estimated_cost=base_budget * 1.05,
                target_calories=base_calories * 1.1,
                features=["학생 선호 메뉴 70% 반영", "트렌디한 퓨전 메뉴", "SNS 인증샷 고려"],
                pros=["높은 섭취율 보장", "잔반량 획기적 감소", "학생 만족도 극대화", "급식 이미지 개선"],
                cons=["영양 편중 위험성", "건강한 식습관 형성 제약", "메뉴 다양성 제한"],
                risks=["장기적 영양 불균형", "편식 습관 강화"],
                strategy_params={
                    "student_preference_weight": 0.7, "trendy_menu": True, "social_media_ready": True,
                    "satisfaction_priority": True, "waste_minimization": True
                }
            ),
            MenuAlternative(
                id=4,
                title="로컬푸드 계절 전략",
                description="지역 농산물과 제철 식재료를 활용한 신선하고 지속가능한 친환경 식단",
                estimated_cost=base_budget * 0.95,
                target_calories=base_calories,
                features=["지역 농산물 우선", "제철 식재료 100%", "푸드 마일리지 최소화"],
                pros=["최고 신선도 보장", "지역 경제 활성화", "환경 친화적", "교육적 가치"],
                cons=["계절별 메뉴 제한", "공급업체 의존도", "기후 변화 민감성"],
                risks=["자연재해 공급 차질", "가격 변동성 높음"],
                strategy_params={
                    "local_food_ratio": 0.8, "seasonal_priority": True, "environmental_focus": True,
                    "supplier_diversity": True, "educational_value": True
                }
            ),
            MenuAlternative(
                id=5,
                title="글로벌 퓨전 전략",
                description="세계 각국의 건강한 전통 요리를 급식에 접목한 창의적이고 교육적인 식단",
                estimated_cost=base_budget * 1.15,
                target_calories=base_calories * 1.02,
                features=["월별 국가 테마", "문화교육 연계", "새로운 맛 경험"],
                pros=["글로벌 감각 향상", "문화적 다양성 교육", "창의적 메뉴", "차별화된 급식"],
                cons=["높은 식재료 비용", "조리법 복잡성", "학생 적응 시간 필요"],
                risks=["예산 초과 심각", "조리 실패 위험성"],
                strategy_params={
                    "international_menu_ratio": 0.4, "cultural_education": True, "premium_ingredients": True,
                    "cooking_complexity": "high", "adaptation_period": True
                }
            )
        ]
        
        return alternatives

# 전역 서비스 인스턴스
llm_strategy_service = LLMStrategyService()