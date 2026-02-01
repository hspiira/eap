/**
 * Loading Spinner Component
 * Reusable loading spinner with customizable size and color
 */

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  color?: 'safe' | 'natural' | 'nurturing' | 'white'
  className?: string
}

const sizeClasses = {
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-3',
  xl: 'w-12 h-12 border-4',
}

const colorClasses = {
  safe: 'border-safe border-t-transparent',
  natural: 'border-natural border-t-transparent',
  nurturing: 'border-nurturing border-t-transparent',
  white: 'border-white border-t-transparent',
}

export function LoadingSpinner({
  size = 'md',
  color = 'safe',
  className = '',
}: LoadingSpinnerProps) {
  return (
    <div
      className={`inline-block ${sizeClasses[size]} ${colorClasses[color]} rounded-none animate-spin ${className}`}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}
