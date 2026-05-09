/**
 * Browser localStorage — three namespaced keys, typed access.
 *
 *   evexia.auth   → { token, refresh_token, user_id, email }
 *   evexia.tenant → { id }
 *   evexia.ui     → { theme, session_timeout_minutes }
 *
 * No other module in the codebase should touch `localStorage` directly.
 */

const KEY_AUTH = 'evexia.auth'
const KEY_TENANT = 'evexia.tenant'
const KEY_UI = 'evexia.ui'

function readJson<T>(key: string): Partial<T> {
  if (typeof window === 'undefined') return {}
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as unknown
    return parsed && typeof parsed === 'object' ? (parsed as Partial<T>) : {}
  } catch (_err) {
    return {}
  }
}

function writeJson<T>(key: string, value: T): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch (_err) {
    // quota exceeded or storage disabled — ignore
  }
}

function remove(key: string): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.removeItem(key)
  } catch (_err) {
    // quota exceeded or storage disabled — ignore
  }
}

export interface AuthRecord {
  token: string | null
  refresh_token: string | null
  user_id: string | null
  email: string | null
  /** Epoch ms when the access token expires. Null when unknown (cookie auth). */
  token_expires_at: number | null
  /** Optional CSRF token, used when BE sets HttpOnly auth cookies. */
  csrf_token: string | null
}

const EMPTY_AUTH: AuthRecord = {
  token: null,
  refresh_token: null,
  user_id: null,
  email: null,
  token_expires_at: null,
  csrf_token: null,
}

export const authStorage = {
  read(): AuthRecord {
    return { ...EMPTY_AUTH, ...readJson<AuthRecord>(KEY_AUTH) }
  },
  patch(partial: Partial<AuthRecord>): AuthRecord {
    const next = { ...this.read(), ...partial }
    writeJson(KEY_AUTH, next)
    return next
  },
  clear(): void {
    remove(KEY_AUTH)
  },
}

export interface TenantRecord {
  id: string | null
}

export const tenantStorage = {
  readId(): string | null {
    return readJson<TenantRecord>(KEY_TENANT).id ?? null
  },
  writeId(id: string | null): void {
    if (id) writeJson<TenantRecord>(KEY_TENANT, { id })
    else remove(KEY_TENANT)
  },
  clear(): void {
    remove(KEY_TENANT)
  },
}

export interface UiPrefs {
  theme: 'light' | 'dark' | 'system'
  session_timeout_minutes: number
  sidebar_open: boolean
}

const DEFAULT_UI: UiPrefs = {
  theme: 'system',
  session_timeout_minutes: 30,
  sidebar_open: false,
}

export const uiStorage = {
  read(): UiPrefs {
    const stored = readJson<UiPrefs>(KEY_UI)
    return {
      theme:
        stored.theme === 'light' || stored.theme === 'dark' || stored.theme === 'system'
          ? stored.theme
          : DEFAULT_UI.theme,
      session_timeout_minutes:
        typeof stored.session_timeout_minutes === 'number' &&
        stored.session_timeout_minutes > 0
          ? stored.session_timeout_minutes
          : DEFAULT_UI.session_timeout_minutes,
      sidebar_open:
        typeof stored.sidebar_open === 'boolean'
          ? stored.sidebar_open
          : DEFAULT_UI.sidebar_open,
    }
  },
  patch(partial: Partial<UiPrefs>): UiPrefs {
    const next = { ...this.read(), ...partial }
    writeJson(KEY_UI, next)
    return next
  },
}
