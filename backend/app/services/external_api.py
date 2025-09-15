
# backend/app/services/external_api.py
import httpx
import logging

logger = logging.getLogger(__name__)

class ExternalAPIService:
    """외부 API 연동 서비스"""
    
    def __init__(self):
        self.client = httpx.AsyncClient()
        logger.info("ExternalAPIService 초기화")
    
    async def call_external_api(self, url: str, method: str = "GET", data: dict = None):
        """외부 API 호출"""
        try:
            # TODO: 실제 API 호출 로직 구현
            if method == "GET":
                response = await self.client.get(url)
            elif method == "POST":
                response = await self.client.post(url, json=data)
            else:
                raise ValueError(f"지원하지 않는 메소드: {method}")
                
            logger.info(f"외부 API 호출: {url} - 상태: {response.status_code}")
            return response.json()
            
        except Exception as e:
            logger.error(f"외부 API 호출 실패: {e}")
            raise
    
    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()

# 전역 외부 API 서비스
external_api_service = ExternalAPIService()