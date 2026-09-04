/**
 * One place for the "come back here after sign-in" path.
 *
 * Four call sites have to agree: the guards that capture where the user was
 * (RequireAuth, AppBootstrap's 401 handler) and the screens that send them
 * back (login, sso, the Azure callback). They used to disagree — the guards
 * captured `window.location.pathname` and dropped the query string, login
 * navigated with `search: {}`, and each screen validated `?redirect=` its own
 * way, from strict to not at all. Expiring on `/me?view=at-risk` returned you
 * to `/me` on the default view.
 */

/** Auth screens are never a destination — sending a user back to one loops. */
const AUTH_PATHS = new Set(["/auth/login", "/auth/set-password", "/auth/sso"])

function isAuthPath(pathname: string): boolean {
  return AUTH_PATHS.has(pathname) || pathname.startsWith("/auth/azure")
}

/**
 * Where the user is now, as a relative path with query string and hash, or
 * undefined when there is nowhere worth returning to — an auth screen, or SSR
 * where there is no location at all.
 */
export function currentRedirectPath(): string | undefined {
  if (typeof window === "undefined") return undefined
  const { pathname, search, hash } = window.location
  if (isAuthPath(pathname)) return undefined
  return `${pathname}${search}${hash}`
}

/**
 * Validate an untrusted `?redirect=` value, preserving its query and hash.
 *
 * Same-origin relative paths only: an absolute URL or a protocol-relative
 * `//evil.com` is an open redirect, and a backslash counts because browsers
 * normalise `/\evil.com` to `//evil.com`. Auth screens are rejected as loops.
 * The auth-screen test reads the pathname alone, so `/auth/login?next=x` is
 * turned away the same as a bare `/auth/login`.
 */
export function safeRedirectPath(raw: unknown): string | undefined {
  const s = typeof raw === "string" ? raw.trim() : ""
  if (!s || !s.startsWith("/")) return undefined
  if (s.startsWith("//") || s.startsWith("/\\")) return undefined
  if (isAuthPath(s.split(/[?#]/, 1)[0])) return undefined
  return s
}

/**
 * Split a redirect path into the three parts `navigate()` takes, so the query
 * string survives the trip. Repeated keys (`?a=1&a=2`) collapse to the last
 * value; no route in this app reads a param more than once.
 */
export function redirectTarget(path: string): {
  to: string
  search: Record<string, string>
  hash: string | undefined
} {
  const hashAt = path.indexOf("#")
  const hash = hashAt >= 0 ? path.slice(hashAt + 1) : undefined
  const pathAndQuery = hashAt >= 0 ? path.slice(0, hashAt) : path

  const queryAt = pathAndQuery.indexOf("?")
  const to = queryAt >= 0 ? pathAndQuery.slice(0, queryAt) : pathAndQuery
  const query = queryAt >= 0 ? pathAndQuery.slice(queryAt + 1) : ""

  return { to, search: Object.fromEntries(new URLSearchParams(query)), hash: hash || undefined }
}
