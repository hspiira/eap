/**
 * Schedules a silent refresh of the access token shortly before it expires.
 * Reads `token_expires_at` from authStorage; if missing, no-op (e.g. cookie auth where
 * the BE rotates server-side and `expires_in` isn't surfaced to the FE).
 */

import { useEffect } from 'react'

import apiClient from '@/api/client'
import { useAuthStore } from '@/store/slices/authSlice'

const REFRESH_BEFORE_EXPIRY_MS = 60_000 // refresh 1 min before expiry
const MIN_DELAY_MS = 5_000

export function useSilentRefresh() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const token = useAuthStore((s) => s.token)

  useEffect(() => {
    if (!isAuthenticated || !token) return

    const expiresAt = apiClient.getTokenExpiresAt()
    if (!expiresAt) return

    const now = Date.now()
    const fireAt = expiresAt - REFRESH_BEFORE_EXPIRY_MS
    const delay = Math.max(MIN_DELAY_MS, fireAt - now)

    const timeoutId = setTimeout(() => {
      void apiClient.refreshAccessToken().then((ok) => {
        if (!ok) {
          useAuthStore.getState().clearAuth()
        }
      })
    }, delay)

    return () => clearTimeout(timeoutId)
  }, [isAuthenticated, token])
}
