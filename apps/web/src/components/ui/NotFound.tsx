import { Link } from '@tanstack/react-router'
import { ArrowLeft, FileQuestion, Home } from 'lucide-react'

export interface NotFoundProps {
  title?: string
  message?: string
  showBackButton?: boolean
  backUrl?: string
  backLabel?: string
  fullPage?: boolean
  className?: string
}

export function NotFound({
  title = 'Page not found',
  message = "The page you're looking for doesn't exist or has been moved.",
  showBackButton = true,
  backUrl = '/',
  backLabel = 'Go to dashboard',
  fullPage = false,
  className = '',
}: NotFoundProps) {
  const actions = showBackButton && (
    <div className={fullPage ? 'flex flex-col gap-3' : 'flex flex-wrap gap-4 justify-center'}>
      <Link
        to={backUrl}
        className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary text-white hover:opacity-90 font-semibold rounded-none transition-opacity"
      >
        <Home size={18} aria-hidden />
        <span>{backLabel}</span>
      </Link>
      <button
        type="button"
        onClick={() => window.history.back()}
        className={`inline-flex items-center justify-center gap-2 px-6 py-3 font-semibold rounded-none transition-colors ${
          fullPage ? 'bg-warning text-white hover:opacity-90' : 'bg-muted/10 text-fg-muted hover:bg-muted/20'
        }`}
      >
        <ArrowLeft size={18} aria-hidden />
        <span>Go back</span>
      </button>
    </div>
  )

  if (fullPage) {
    return (
      <div className={`min-h-screen bg-white flex items-center justify-center px-4 ${className}`}>
        <div className="max-w-md w-full bg-white border border-safe p-8 rounded-none">
          <div className="text-center">
            <FileQuestion size={48} className="text-fg-muted mx-auto mb-4" aria-hidden />
            <h1 className="text-2xl font-bold text-fg-muted mb-2">{title}</h1>
            <p className="text-fg-muted/80 mb-6">{message}</p>
            {actions}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex flex-col items-center justify-center min-h-[60vh] p-8 text-center ${className}`}>
      <div className="mb-8">
        <p className="text-6xl font-bold text-fg-muted mb-4">404</p>
        <h1 className="text-2xl font-semibold text-fg-muted mb-4">{title}</h1>
        <p className="text-fg-muted/80 max-w-md mx-auto">{message}</p>
      </div>
      {actions}
    </div>
  )
}
