// frontend/src/components/ui/Card.tsx
import { cn } from '@/lib/utils'
import type { CardProps } from '@/types'

export function Card({ children, title, className = '' }: CardProps) {
  return (
    <div className={cn('bg-white rounded-lg shadow p-6', className)}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {title}
        </h3>
      )}
      {children}
    </div>
  )
}
