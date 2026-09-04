import { useEffect } from "react"

import { useNavigate } from "@tanstack/react-router"

import { redirectTarget } from "@/lib/redirect"
import { useAuthStore } from "@/store/slices/authSlice"

/**
 * Redirects authenticated users to the given path (default '/').
 * Used on login/signup pages so already-authenticated users are sent to app.
 */
export function useRedirectIfAuthenticated(redirectTo = "/") {
  const navigate = useNavigate()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  useEffect(() => {
    if (isAuthenticated) {
      const target = redirectTarget(redirectTo)
      navigate({ to: target.to, search: target.search, hash: target.hash })
    }
  }, [isAuthenticated, navigate, redirectTo])

  return isAuthenticated
}
