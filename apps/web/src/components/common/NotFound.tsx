/**
 * Not Found Component
 * 404 page component. Use fullPage for router notFoundComponent (ErrorBoundary-style layout).
 */

import { Link } from '@tanstack/react-router'
import { Home, ArrowLeft, FileQuestion } from 'lucide-react'

export interface NotFoundProps {
  title?: string
  message?: string
  showBackButton?: boolean
  backUrl?: string
  backLabel?: string
  /** When true, renders full-screen card layout like ErrorBoundary fallback. */
  fullPage?: boolean
  className?: string
}

export function NotFound({
  title = 'Page Not Found',
  message = "The page you're looking for doesn't exist or has been moved.",
  showBackButton = true,
  backUrl = '/',
  backLabel = 'Go Home',
  fullPage = false,
  className = '',
}: NotFoundProps) {
  const actions = showBackButton && (
    <div className={fullPage ? 'flex flex-col gap-3' : 'flex gap-4'}>
      <Link
        to={backUrl}
        className="flex items-center justify-center gap-2 px-6 py-3 bg-primary hover:bg-primary-hover text-white font-semibold rounded-none transition-colors"
      >
        <Home size={18} />
        <span>{backLabel}</span>
      </Link>
      <button
        type="button"
        onClick={() => window.history.back()}
        className={`flex items-center justify-center gap-2 px-6 py-3 rounded-none transition-colors font-semibold ${
          fullPage
            ? 'bg-nurturing hover:bg-nurturing-dark text-white'
            : 'bg-neutral hover:bg-neutral-dark text-white'
        }`}
      >
        <ArrowLeft size={18} />
        <span>Go Back</span>
      </button>
    </div>
  )

  if (fullPage) {
    return (
      <div className={`min-h-screen bg-page flex items-center justify-center px-4 ${className}`}>
        <div className="max-w-md w-full bg-surface p-8 rounded-none border border-[0.5px] border-border">
          <div className="text-center">
            <FileQuestion size={48} className="text-safe mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-text mb-2">{title}</h1>
            <p className="text-text-muted tracking-wider mb-6">{message}</p>
            {actions}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      className={`flex flex-col items-center justify-center min-h-[60vh] p-8 text-center ${className}`}
    >
      <div className="mb-8">
        <h1 className="text-6xl font-bold text-text mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-text mb-4">{title}</h2>
        <p className="text-text-muted max-w-md mx-auto">{message}</p>
      </div>
      {actions}
    </div>
  )
}
