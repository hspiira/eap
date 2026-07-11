import { Link } from '@tanstack/react-router'
import { ArrowLeft, FileQuestion, Home } from 'lucide-react'

import { Button } from '@/components/ui/button'

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
    <div className="flex flex-col sm:flex-row gap-3 justify-center">
      <Button asChild>
        <Link to={backUrl}>
          <Home size={16} aria-hidden />
          {backLabel}
        </Link>
      </Button>
      <Button variant="outline" onClick={() => window.history.back()}>
        <ArrowLeft size={16} aria-hidden />
        Go back
      </Button>
    </div>
  )

  return (
    <div
      className={`min-h-screen bg-bg flex items-center justify-center px-4 ${className}`}
    >
      <div className="max-w-sm w-full text-center">
        <FileQuestion size={48} className="text-fg-subtle mx-auto mb-6" aria-hidden />
        <h1 className="text-2xl font-semibold text-fg mb-2">{title}</h1>
        <p className="text-fg-muted mb-8 text-sm leading-relaxed">{message}</p>
        {actions}
      </div>
    </div>
  )
}
