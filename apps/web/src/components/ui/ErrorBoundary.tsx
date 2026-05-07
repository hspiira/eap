import { Component, type ReactNode } from 'react'

import { Link } from '@tanstack/react-router'
import { AlertCircle, Home } from 'lucide-react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught:', error, errorInfo)
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen bg-white flex items-center justify-center px-4">
          <div className="max-w-md w-full bg-white border border-safe p-8 rounded-none">
            <div className="text-center">
              <AlertCircle size={48} className="text-danger mx-auto mb-4" aria-hidden />
              <h1 className="text-2xl font-bold text-safe mb-2">Something went wrong</h1>
              <p className="text-safe/80 mb-6">
                An unexpected error occurred. Try refreshing the page or return to the dashboard.
              </p>

              {this.state.error && import.meta.env.DEV && (
                <div className="mb-6 p-3 bg-safe/10 border border-safe rounded-none text-left">
                  <p className="text-safe text-xs font-mono break-all">{this.state.error.message}</p>
                </div>
              )}

              <div className="flex flex-col gap-3">
                <button
                  type="button"
                  onClick={this.handleReset}
                  className="px-6 py-3 bg-natural text-white hover:opacity-90 font-semibold rounded-none transition-opacity"
                >
                  Try again
                </button>
                <Link
                  to="/"
                  className="flex items-center justify-center gap-2 px-6 py-3 bg-nurturing text-white hover:opacity-90 font-semibold rounded-none transition-opacity"
                >
                  <Home size={18} aria-hidden />
                  Go to dashboard
                </Link>
              </div>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
