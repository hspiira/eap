/**
 * JWT Utility
 * Helper functions for working with JWT tokens
 */

/**
 * Decode JWT token payload without verification
 * Returns the decoded payload or null if invalid
 */
export function decodeJWT(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) {
      return null
    }

    // Decode the payload (second part)
    const payload = parts[1]
    // Replace URL-safe base64 characters
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    // Add padding if needed
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4)
    // Decode
    const decoded = atob(padded)
    return JSON.parse(decoded) as Record<string, unknown>
  } catch {
    return null
  }
}

/**
 * Extract user_id from JWT token
 * Checks common JWT claim fields: sub, user_id, id
 */
export function getUserIdFromToken(token: string | null): string | null {
  if (!token) return null

  const payload = decodeJWT(token)
  if (!payload) return null

  // Check common JWT claim fields
  return (
    (payload.sub as string) ||
    (payload.user_id as string) ||
    (payload.id as string) ||
    null
  )
}
