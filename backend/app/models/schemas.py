# backend/app/models/schemas.py
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

# ========== 기본 응답 스키마 ==========
class BaseResponse(BaseModel):
    message: str
    success: bool = True
    timestamp: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorResponse(BaseModel):
    message: str
    success: bool = False
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

# ========== 예시 데이터 스키마 (필요시 수정/삭제) ==========
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# TODO: 실제 프로젝트에 맞는 스키마들 추가
# 예시:
# - User 관련 스키마
# - Product 관련 스키마  
# - Order 관련 스키마
# - 기타 비즈니스 로직 스키마