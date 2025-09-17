# backend/app/services/natural_language.py
"""
자연어 입력을 통한 파라미터 변경 처리 서비스
"가격 500원 올려줘", "칼로리 높여줘" 등의 입력을 파싱
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParameterChange:
    """파라미터 변경 정보"""
    parameter: str  # days, budget, calories, etc.
    action: str     # increase, decrease, set
    value: Optional[float] = None
    unit: Optional[str] = None
    confidence: float = 1.0

class NaturalLanguageProcessor:
    """자연어 파라미터 변경 처리기"""
    
    def __init__(self):
        # 파라미터 키워드 맵핑
        self.parameter_keywords = {
            'budget': ['가격', '예산', '비용', '돈', '원', 'budget', 'cost', 'price'],
            'calories': ['칼로리', 'kcal', '칼', 'cal', 'calories', '열량'],
            'days': ['일수', '기간', '날', '일', 'days', 'period', '주', 'week'],
            'protein': ['단백질', 'protein', '프로틴'],
            'carbs': ['탄수화물', '탄수', 'carb', 'carbohydrate'],
            'fat': ['지방', 'fat'],
            'sodium': ['나트륨', 'sodium', '염분', '소금'],
            'portions': ['인분', '양', 'portion', 'serving']
        }
        
        # 액션 키워드 맵핑
        self.action_keywords = {
            'increase': ['올려', '높여', '증가', '늘려', '키워', 'up', 'increase', 'raise', 'boost', '더', '많이'],
            'decrease': ['내려', '낮춰', '감소', '줄여', 'down', 'decrease', 'reduce', 'lower', '적게', '덜'],
            'set': ['로', '으로', '를', '을', 'set', 'to', '맞춰', '설정']
        }
        
        # 숫자 추출 패턴
        self.number_patterns = [
            r'(\d+(?:\.\d+)?)\s*(원|kcal|일|주|주간|개월|달|명|인분|g|kg)',
            r'(\d+(?:\.\d+)?)\s*([가-힣]+)',
            r'(\d+(?:\.\d+)?)',
        ]
        
        # 상대적 변경 키워드
        self.relative_keywords = {
            'much_more': ['많이', '대폭', '크게', '훨씬', '상당히'],
            'little_more': ['조금', '약간', '살짝', '소폭'],
            'double': ['두배', '2배', 'double'],
            'half': ['절반', '반', 'half']
        }
        
        logger.info("NaturalLanguageProcessor 초기화")

    def process_input(self, natural_input: str, current_params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        자연어 입력을 처리하여 파라미터 변경사항 적용
        
        Args:
            natural_input: 자연어 입력 ("가격 500원 올려줘")
            current_params: 현재 파라미터 값들
            
        Returns:
            (updated_params, change_log): 업데이트된 파라미터와 변경 로그
        """
        try:
            logger.info(f"자연어 처리 시작: '{natural_input}'")
            
            # 입력 텍스트 정규화
            normalized_input = self._normalize_text(natural_input)
            
            # 파라미터 변경사항 추출
            changes = self._extract_parameter_changes(normalized_input)
            
            # 현재 파라미터에 변경사항 적용
            updated_params = current_params.copy()
            change_log = []
            
            for change in changes:
                old_value = updated_params.get(change.parameter)
                new_value = self._apply_change(old_value, change)
                
                if new_value != old_value:
                    updated_params[change.parameter] = new_value
                    change_log.append(
                        f"{self._get_param_korean_name(change.parameter)}: "
                        f"{old_value} → {new_value} ({change.action})"
                    )
                    logger.info(f"파라미터 변경: {change.parameter} {old_value} → {new_value}")
            
            if not change_log:
                change_log.append("인식된 변경사항이 없습니다.")
                
            return updated_params, change_log
            
        except Exception as e:
            logger.error(f"자연어 처리 실패: {e}")
            return current_params, [f"처리 중 오류: {str(e)}"]

    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        # 소문자 변환 및 공백 정리
        text = text.lower().strip()
        # 특수문자 정리
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    def _extract_parameter_changes(self, text: str) -> List[ParameterChange]:
        """파라미터 변경사항 추출"""
        changes = []
        
        # 각 파라미터에 대해 검사
        for param, keywords in self.parameter_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    change = self._parse_parameter_change(text, param, keyword)
                    if change:
                        changes.append(change)
                        break  # 첫 번째 매칭된 키워드만 사용
        
        return changes

    def _parse_parameter_change(self, text: str, parameter: str, keyword: str) -> Optional[ParameterChange]:
        """특정 파라미터의 변경사항 파싱"""
        try:
            # 키워드 주변 텍스트 추출
            keyword_index = text.find(keyword)
            context = text[max(0, keyword_index-10):keyword_index+len(keyword)+20]
            
            # 액션 타입 결정
            action = self._determine_action(context)
            
            # 숫자 추출
            value, unit = self._extract_number_and_unit(context)
            
            # 상대적 변경량 처리
            if not value:
                value = self._get_relative_value(context, parameter)
            
            return ParameterChange(
                parameter=parameter,
                action=action,
                value=value,
                unit=unit,
                confidence=0.8  # 기본 신뢰도
            )
            
        except Exception as