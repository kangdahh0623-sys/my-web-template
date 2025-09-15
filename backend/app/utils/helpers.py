# backend/app/utils/helpers.py
import hashlib
import uuid
import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

def generate_id() -> str:
    """고유 ID 생성"""
    return str(uuid.uuid4())

def generate_short_id() -> str:
    """짧은 ID 생성 (8자리)"""
    return str(uuid.uuid4())[:8]

def hash_password(password: str) -> str:
    """패스워드 해시 (간단 버전)"""
    # TODO: 실제 프로덕션에서는 bcrypt 등 사용
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """패스워드 검증"""
    return hash_password(password) == hashed

def get_current_timestamp() -> str:
    """현재 시간 ISO 형식으로 반환"""
    return datetime.now().isoformat()

def format_response(data: Any, message: str = "Success") -> dict:
    """표준 응답 형식"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": get_current_timestamp()
    }

def format_error(message: str, error: Optional[str] = None) -> dict:
    """표준 에러 응답 형식"""
    return {
        "success": False,
        "message": message,
        "error": error,
        "timestamp": get_current_timestamp()
    }

def log_request(endpoint: str, method: str, user_id: Optional[str] = None):
    """요청 로그"""
    logger.info(f"API 요청: {method} {endpoint} - 사용자: {user_id or 'anonymous'}")

def sanitize_input(text: str) -> str:
    """입력 데이터 정리"""
    # TODO: XSS 방지, SQL 인젝션 방지 등
    return text.strip()

# TODO: 프로젝트에 맞는 추가 유틸리티 함수들
# 예시:
# - 파일 업로드 처리
# - 이메일 검증
# - 전화번호 포맷팅
# - 데이터 변환 함수
# - API 키 생성/검증