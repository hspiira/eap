import { beforeEach, describe, expect, it } from 'vitest'

import { authStorage, tenantStorage, uiStorage } from '@/lib/storage'

describe('authStorage', () => {
  beforeEach(() => window.localStorage.clear())

  it('returns nulls when nothing is stored', () => {
    const r = authStorage.read()
    expect(r).toEqual({
      token: null,
      refresh_token: null,
      user_id: null,
      email: null,
      token_expires_at: null,
      csrf_token: null,
    })
  })

  it('round-trips a write', () => {
    authStorage.patch({ token: 't', user_id: 'u', email: 'e@x' })
    const r = authStorage.read()
    expect(r.token).toBe('t')
    expect(r.user_id).toBe('u')
    expect(r.email).toBe('e@x')
  })

  it('patch is partial — keeps unrelated keys', () => {
    authStorage.patch({ token: 't' })
    authStorage.patch({ user_id: 'u' })
    const r = authStorage.read()
    expect(r.token).toBe('t')
    expect(r.user_id).toBe('u')
  })

  it('clear wipes the namespace', () => {
    authStorage.patch({ token: 't', user_id: 'u' })
    authStorage.clear()
    expect(authStorage.read().token).toBeNull()
    expect(authStorage.read().user_id).toBeNull()
  })

  it('survives corrupted JSON in storage', () => {
    window.localStorage.setItem('evexia.auth', 'not-json{')
    expect(authStorage.read().token).toBeNull()
  })

  it('survives non-object JSON in storage', () => {
    window.localStorage.setItem('evexia.auth', '"a-string"')
    expect(authStorage.read().token).toBeNull()
  })

  it('round-trips token_expires_at', () => {
    const at = Date.now() + 120_000
    authStorage.patch({ token: 't', token_expires_at: at })
    expect(authStorage.read().token_expires_at).toBe(at)
  })

  it('round-trips csrf_token', () => {
    authStorage.patch({ csrf_token: 'csrf-abc' })
    expect(authStorage.read().csrf_token).toBe('csrf-abc')
  })
})

describe('tenantStorage', () => {
  beforeEach(() => window.localStorage.clear())

  it('readId returns null when empty', () => {
    expect(tenantStorage.readId()).toBeNull()
  })

  it('writeId + readId round-trip', () => {
    tenantStorage.writeId('tenant-abc')
    expect(tenantStorage.readId()).toBe('tenant-abc')
  })

  it('writeId(null) removes the entry', () => {
    tenantStorage.writeId('tenant-abc')
    tenantStorage.writeId(null)
    expect(tenantStorage.readId()).toBeNull()
  })

  it('clear removes the entry', () => {
    tenantStorage.writeId('tenant-abc')
    tenantStorage.clear()
    expect(tenantStorage.readId()).toBeNull()
  })
})

describe('uiStorage', () => {
  beforeEach(() => window.localStorage.clear())

  it('returns defaults when empty', () => {
    const r = uiStorage.read()
    expect(r.theme).toBe('system')
    expect(r.session_timeout_minutes).toBe(30)
  })

  it('round-trips theme and session timeout', () => {
    uiStorage.patch({ theme: 'dark', session_timeout_minutes: 60 })
    const r = uiStorage.read()
    expect(r.theme).toBe('dark')
    expect(r.session_timeout_minutes).toBe(60)
  })

  it('falls back to default on invalid theme', () => {
    window.localStorage.setItem('evexia.ui', JSON.stringify({ theme: 'banana' }))
    expect(uiStorage.read().theme).toBe('system')
  })

  it('falls back to default on invalid timeout', () => {
    window.localStorage.setItem('evexia.ui', JSON.stringify({ session_timeout_minutes: -5 }))
    expect(uiStorage.read().session_timeout_minutes).toBe(30)
  })

  it('patch merges with existing prefs', () => {
    uiStorage.patch({ theme: 'dark' })
    uiStorage.patch({ session_timeout_minutes: 45 })
    const r = uiStorage.read()
    expect(r.theme).toBe('dark')
    expect(r.session_timeout_minutes).toBe(45)
  })
})
