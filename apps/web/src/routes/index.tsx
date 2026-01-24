import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { AppLayout } from '@/components/layout/AppLayout'
import { useEffect } from 'react'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  const { isAuthenticated, isLoading, logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      // Redirect authenticated users to dashboard (to be created)
      // For now, keep them on home page
    }
  }, [isAuthenticated, isLoading])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-calm flex items-center justify-center">
        <div className="text-safe">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-calm">
        <div className="max-w-4xl mx-auto px-6 py-16">
          {/* Header */}
          <div className="text-center mb-16">
            <h1 className="text-5xl font-bold text-safe mb-4">Evexía</h1>
            <p className="text-xl text-safe-light">Management Platform</p>
          </div>

          {/* Main Content */}
          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <div className="bg-calm border border-[0.5px] border-safe/30 p-8">
              <h2 className="text-2xl font-semibold text-safe mb-4">Sign In</h2>
              <p className="text-safe-light mb-6">
                Access your account to manage your organization, users, and services.
              </p>
              <Link
                to="/auth/login"
                search={{}}
                className="inline-block w-full px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold text-center rounded-none transition-colors"
              >
                Sign In
              </Link>
            </div>

            <div className="bg-calm border border-[0.5px] border-safe/30 p-8">
              <h2 className="text-2xl font-semibold text-safe mb-4">Get Started</h2>
              <p className="text-safe-light mb-6">
                Create an organization and start managing your services today.
              </p>
              <Link
                to="/auth/signup"
                className="inline-block w-full px-6 py-3 bg-nurturing hover:bg-nurturing-dark text-white font-semibold text-center rounded-none transition-colors"
              >
                Sign Up
              </Link>
            </div>
          </div>

          {/* Footer Info */}
          <div className="text-center text-sm text-safe-light">
            <p>Platform for service management and delivery</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-safe mb-6">Dashboard</h1>
        <p className="text-safe-light">
          Welcome to Evexía. Select a section from the sidebar to get started.
        </p>
      </div>
    </AppLayout>
  )
}
