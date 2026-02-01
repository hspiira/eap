/**
 * Not Found Component
 * 404 page component
 */

import { Link } from '@tanstack/react-router'
import { Home, ArrowLeft } from 'lucide-react'

export interface NotFoundProps {
  title?: string
  message?: string
  showBackButton?: boolean
  backUrl?: string
  backLabel?: string
  className?: string
}

export function NotFound({
  title = 'Page Not Found',
  message = "The page you're looking for doesn't exist or has been moved.",
  showBackButton = true,
  backUrl = '/',
  backLabel = 'Go Home',
  className = '',
}: NotFoundProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center min-h-[60vh] p-8 text-center ${className}`}
    >
      <div className="mb-8">
        <h1 className="text-6xl font-bold text-text mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-text mb-4">{title}</h2>
        <p className="text-text-muted max-w-md mx-auto">{message}</p>
      </div>

      {showBackButton && (
        <div className="flex gap-4">
          <Link
            to={backUrl}
            className="flex items-center gap-2 px-6 py-3 bg-primary hover:bg-primary-hover text-white rounded-none transition-colors"
          >
            <Home size={18} />
            <span>{backLabel}</span>
          </Link>
          <button
            onClick={() => window.history.back()}
            className="flex items-center gap-2 px-6 py-3 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors"
          >
            <ArrowLeft size={18} />
            <span>Go Back</span>
          </button>
        </div>
      )}
    </div>
  )
}
