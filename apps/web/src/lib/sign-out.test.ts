/**
 * Signing out has to leave nothing behind.
 *
 * A client navigation kept the signed-in user's React tree, query cache and
 * module state alive, and left the pages they had open in history as live
 * routes. The full document load is the teardown, so it is the part worth
 * pinning: tear down first, then leave, and replace the authed entry rather
 * than stacking sign-in on top of it.
 */

import { beforeEach, describe, expect, it, vi } from "vitest"

const mocks = vi.hoisted(() => ({
  logout: vi.fn(async () => {}),
  replace: vi.fn(),
  order: [] as string[],
}))

vi.mock("@/lib/auth-store", () => ({
  authActions: {
    logout: async () => {
      mocks.order.push("logout")
      await mocks.logout()
    },
  },
}))

const { signOutAndRedirect, SIGN_IN_PATH } = await import("@/lib/sign-out")

beforeEach(() => {
  vi.clearAllMocks()
  mocks.order = []
  mocks.logout.mockImplementation(async () => {})
  Object.defineProperty(window, "location", {
    configurable: true,
    value: {
      replace: (url: string) => {
        mocks.order.push("replace")
        mocks.replace(url)
      },
      assign: vi.fn(),
      href: "http://localhost/clients",
    },
  })
})

describe("signOutAndRedirect", () => {
  it("leaves through a full document load at the sign-in page", async () => {
    await signOutAndRedirect()

    expect(mocks.replace).toHaveBeenCalledWith(SIGN_IN_PATH)
  })

  it("replaces the authed entry rather than pushing sign-in on top of it", async () => {
    await signOutAndRedirect()

    expect(window.location.assign).not.toHaveBeenCalled()
  })

  it("tears the session down before it leaves", async () => {
    await signOutAndRedirect()

    expect(mocks.order).toEqual(["logout", "replace"])
  })

  it("still leaves when teardown throws", async () => {
    // The case where staying put is most dangerous: the session may already be
    // revoked server-side while the page still shows the last user's data.
    mocks.logout.mockRejectedValueOnce(new Error("network"))

    await expect(signOutAndRedirect()).rejects.toThrow("network")
    expect(mocks.replace).toHaveBeenCalledWith(SIGN_IN_PATH)
  })
})
