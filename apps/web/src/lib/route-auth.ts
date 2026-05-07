/**
 * Route-level auth guard for TanStack Router.
 * Use as beforeLoad on protected routes to redirect unauthenticated users to login
 * before any component or loader runs (no token = redirect).
 *
 * On the server (SSR) we never redirect; let the client run after hydration.
 */

import { redirect } from '@tanstack/react-router'

import apiClient from '@/api/client'

function safeRedirectPath(path: string): string {
  const p = path?.trim() || '/'
  if (p === '/auth/login' || p === '/auth/signup' || p === '/auth/set-password') return '/'
  return p.startsWith('/') && !p.startsWith('//') ? p : '/'
}

export function requireAuthBeforeLoad(intendedPath?: string): void {
  if (typeof window === 'undefined') return
  const token = apiClient.getToken()
  if (!token) {
    const redirectPath = safeRedirectPath(
      intendedPath ?? window.location.pathname
    )
    throw redirect({
      to: '/auth/login',
      search: { redirect: redirectPath },
      replace: true,
    })
  }
}
