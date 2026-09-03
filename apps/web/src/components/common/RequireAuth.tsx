import { type ReactNode,useEffect } from 'react'

import { useNavigate } from '@tanstack/react-router'
import { Loader2 } from 'lucide-react'

import { useAuthStore } from '@/store/slices/authSlice'

interface RequireAuthProps {
  /** Where to send unauthenticated users. Defaults to /auth/login. */
  loginPath?: string
  /** Path to come back to after sign-in. */
  redirectAfterLogin?: string
  /** Content to render once the user is authenticated. */
  children: ReactNode
}

/**
 * Component-level auth guard.
 *
 * Renders the children only when the auth store reports an authenticated session.
 * While initAuth() is still resolving (bearer or cookie mode) we render a spinner
 * instead of flashing the children or redirecting prematurely.
 */
export function RequireAuth({
  loginPath = '/auth/login',
  redirectAfterLogin,
  children,
}: RequireAuthProps) {
  const navigate = useNavigate()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const isLoading = useAuthStore((s) => s.isLoading)

  useEffect(() => {
    if (isLoading) return
    if (isAuthenticated) return
    const redirect =
      redirectAfterLogin ??
      (typeof window !== 'undefined' ? window.location.pathname : undefined)
    navigate({
      to: loginPath,
      search: { tenant_code: undefined, email: undefined, redirect },
      replace: true,
    })
  }, [isAuthenticated, isLoading, loginPath, navigate, redirectAfterLogin])

  if (isLoading || !isAuthenticated) {
    return (
      <div
        className="grid min-h-svh w-full place-items-center bg-bg text-fg"
        role="status"
        aria-live="polite"
      >
        <Loader2 className="h-6 w-6 animate-spin text-fg-muted" aria-hidden="true" />
        <span className="sr-only">Loading your session…</span>
      </div>
    )
  }

  return <>{children}</>
}
