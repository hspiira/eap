/**
 * Error Boundary Component
 * Catches React errors and displays a fallback UI
 */

import { Component, ReactNode } from 'react'
import { AlertCircle, Home } from 'lucide-react'
import { Link } from '@tanstack/react-router'

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
    // Log error to console in development
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    }
    // In production, you might want to log to an error reporting service
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
        <div className="min-h-screen bg-calm flex items-center justify-center px-4">
          <div className="max-w-md w-full bg-calm p-8 rounded-none border border-[0.5px] border-safe/30">
            <div className="text-center">
              <AlertCircle size={48} className="text-nurturing mx-auto mb-4" />
              <h1 className="text-2xl font-bold text-safe mb-2">Something went wrong</h1>
              <p className="text-safe-light mb-6">
                An unexpected error occurred. Please try refreshing the page or return to the home page.
              </p>
              
              {this.state.error && import.meta.env.DEV && (
                <div className="mb-6 p-3 bg-calm border-[0.5px] border-safe/30 rounded-none text-left">
                  <p className="text-safe text-xs font-mono break-all">
                    {this.state.error.message}
                  </p>
                </div>
              )}

              <div className="flex flex-col gap-3">
                <button
                  onClick={this.handleReset}
                  className="px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors"
                >
                  Try Again
                </button>
                <Link
                  to="/"
                  className="px-6 py-3 bg-nurturing hover:bg-nurturing-dark text-white font-semibold rounded-none transition-colors flex items-center justify-center gap-2"
                >
                  <Home size={18} />
                  Go to Home
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
