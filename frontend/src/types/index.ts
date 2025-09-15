// frontend/src/types/index.ts

// ========== 기본 타입들 ==========
export interface BaseResponse {
  message: string
  success: boolean
  timestamp?: string
}

export interface ApiError {
  detail: string
}

// ========== 백엔드 API 응답 타입들 ==========
export interface HealthResponse {
  status: string
}

export interface ApiTestResponse {
  message: string
  success: boolean
  timestamp?: string
}

export interface ApiInfoResponse {
  api_name: string
  version: string
  status: string
  endpoints: string[]
}

// ========== 컴포넌트 Props ==========
export interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  type?: 'button' | 'submit' | 'reset'
  variant?: 'primary' | 'secondary' | 'danger'
  disabled?: boolean
  className?: string
}

export interface CardProps {
  children: React.ReactNode
  title?: string
  className?: string
}

export interface LayoutProps {
  children: React.ReactNode
}

// ========== 예시 데이터 타입 (필요시 수정/삭제) ==========
export interface User {
  id: number
  name: string
  email: string
  created_at: string
}

export interface Item {
  id: number
  name: string
  description?: string
  created_at: string
}

// TODO: 프로젝트에 맞는 타입들 추가
// 예시:
// - Product 관련 타입
// - Order 관련 타입
// - 기타 비즈니스 로직 타입