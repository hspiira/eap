import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
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

  return (
    <div className="min-h-screen bg-calm">
      <section className="relative py-20 px-6 text-center overflow-hidden">
        <div className="relative max-w-5xl mx-auto">
          <h1 className="text-6xl md:text-7xl font-black text-safe mb-6 [letter-spacing:-0.08em]">
            Evexía
          </h1>
          <p className="text-2xl md:text-3xl text-safe mb-4 font-light">
            Management Platform
          </p>
          <p className="text-lg text-safe-light max-w-3xl mx-auto mb-8">
            Multi-tenant platform for managing services, clients, contracts, and service delivery.
          </p>
          <div className="flex flex-col items-center gap-4">
            {isAuthenticated ? (
              <>
                <p className="text-safe mb-4">Welcome! You are signed in.</p>
                <button
                  onClick={logout}
                  className="px-8 py-3 bg-nurturing hover:bg-nurturing-dark text-white font-semibold rounded-none transition-colors"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <div className="flex flex-col gap-4 items-center">
                  <div className="flex gap-4">
                    <Link
                      to="/auth/login"
                      search={{}}
                      className="px-8 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors"
                    >
                      Sign In
                    </Link>
                    <Link
                      to="/auth/signup"
                      className="px-8 py-3 bg-nurturing hover:bg-nurturing-dark text-white font-semibold rounded-none transition-colors"
                    >
                      Sign Up
                    </Link>
                  </div>
                  <Link
                    to="/tenants/create"
                    className="px-8 py-3 bg-safe hover:bg-safe-dark text-white font-semibold rounded-none transition-colors"
                  >
                    Create Tenant
                  </Link>
                </div>
                <p className="text-safe-light text-sm mt-2">
                  Backend API: <code className="px-2 py-1 bg-calm-dark text-safe rounded-none">http://localhost:8000</code>
                </p>
              </>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}
