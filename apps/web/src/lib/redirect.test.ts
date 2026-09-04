import { describe, expect, it } from "vitest"

import { currentRedirectPath, redirectTarget, safeRedirectPath } from "@/lib/redirect"

describe("safeRedirectPath", () => {
  it("keeps a relative path with its query string and hash", () => {
    expect(safeRedirectPath("/me?view=at-risk")).toBe("/me?view=at-risk")
    expect(safeRedirectPath("/persons/42?tab=notes#vitals")).toBe("/persons/42?tab=notes#vitals")
  })

  it("trims surrounding whitespace", () => {
    expect(safeRedirectPath("  /me  ")).toBe("/me")
  })

  it("rejects anything that is not a relative path", () => {
    expect(safeRedirectPath("https://evil.com")).toBeUndefined()
    expect(safeRedirectPath("me")).toBeUndefined()
    expect(safeRedirectPath("")).toBeUndefined()
    expect(safeRedirectPath("   ")).toBeUndefined()
  })

  it("rejects protocol-relative paths, backslash form included", () => {
    expect(safeRedirectPath("//evil.com")).toBeUndefined()
    expect(safeRedirectPath("/\\evil.com")).toBeUndefined()
  })

  it("rejects non-string input", () => {
    expect(safeRedirectPath(undefined)).toBeUndefined()
    expect(safeRedirectPath(null)).toBeUndefined()
    expect(safeRedirectPath(42)).toBeUndefined()
    expect(safeRedirectPath({ toString: () => "/me" })).toBeUndefined()
  })

  it("rejects auth screens, which would loop", () => {
    expect(safeRedirectPath("/auth/login")).toBeUndefined()
    expect(safeRedirectPath("/auth/set-password")).toBeUndefined()
    expect(safeRedirectPath("/auth/sso")).toBeUndefined()
    expect(safeRedirectPath("/auth/azure/callback")).toBeUndefined()
  })

  it("rejects an auth screen carrying a query string or hash", () => {
    expect(safeRedirectPath("/auth/login?redirect=/me")).toBeUndefined()
    expect(safeRedirectPath("/auth/login#x")).toBeUndefined()
  })

  it("allows a non-auth path that merely starts with the same letters", () => {
    expect(safeRedirectPath("/authorizations")).toBe("/authorizations")
  })
})

describe("redirectTarget", () => {
  it("splits a bare path", () => {
    expect(redirectTarget("/me")).toEqual({ to: "/me", search: {}, hash: undefined })
  })

  it("splits the query string into search params", () => {
    expect(redirectTarget("/me?view=at-risk")).toEqual({
      to: "/me",
      search: { view: "at-risk" },
      hash: undefined,
    })
  })

  it("splits several params and a hash", () => {
    expect(redirectTarget("/persons?page=2&q=ann#top")).toEqual({
      to: "/persons",
      search: { page: "2", q: "ann" },
      hash: "top",
    })
  })

  it("decodes percent-encoded values", () => {
    expect(redirectTarget("/persons?q=a%20b").search).toEqual({ q: "a b" })
  })

  it("treats an empty query or hash as absent", () => {
    expect(redirectTarget("/me?")).toEqual({ to: "/me", search: {}, hash: undefined })
    expect(redirectTarget("/me#")).toEqual({ to: "/me", search: {}, hash: undefined })
  })

  it("does not mistake a '?' inside the hash for a query string", () => {
    expect(redirectTarget("/me#a?b")).toEqual({ to: "/me", search: {}, hash: "a?b" })
  })
})

describe("currentRedirectPath", () => {
  it("returns pathname, search and hash together", () => {
    window.history.replaceState({}, "", "/me?view=at-risk#vitals")
    expect(currentRedirectPath()).toBe("/me?view=at-risk#vitals")
  })

  it("returns undefined on an auth screen", () => {
    window.history.replaceState({}, "", "/auth/login?redirect=/me")
    expect(currentRedirectPath()).toBeUndefined()
  })

  it("round-trips through safeRedirectPath and redirectTarget", () => {
    window.history.replaceState({}, "", "/persons/42?tab=notes")
    const captured = currentRedirectPath()
    const target = redirectTarget(safeRedirectPath(captured) as string)
    expect(target).toEqual({ to: "/persons/42", search: { tab: "notes" }, hash: undefined })
  })
})
