/**
 * Tabs are navigation, not view state.
 *
 * Opening a tab has to leave a history entry behind, otherwise a whole detail
 * page collapses into one entry and back jumps straight out to the list from
 * wherever in the page the user had got to. That was the reported bug, so the
 * push is pinned here rather than left to the next person's judgement.
 */

import { act, renderHook } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { useTabSearchParam } from "@/hooks/useTabSearchParam"

const navigate = vi.fn()
let search: Record<string, unknown> = {}

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => navigate,
  useSearch: () => search,
}))

type Tab = "overview" | "feedback" | "history"
const TABS: ReadonlyArray<Tab> = ["overview", "feedback", "history"]

function setup(current: Record<string, unknown> = {}) {
  search = current
  navigate.mockClear()
  return renderHook(() => useTabSearchParam<Tab>(TABS, "overview"))
}

/** The search the hook asked the router to write. */
function writtenSearch() {
  const opts = navigate.mock.calls.at(-1)?.[0] as {
    search: (prev: Record<string, unknown>) => Record<string, unknown>
  }
  return opts.search(search)
}

describe("useTabSearchParam", () => {
  it("pushes an entry so back returns to the tab the user came from", () => {
    const { result } = setup()

    act(() => result.current[1]("feedback"))

    expect(navigate).toHaveBeenCalledTimes(1)
    expect(navigate.mock.calls[0][0]).not.toMatchObject({ replace: true })
    expect(writtenSearch()).toMatchObject({ tab: "feedback" })
  })

  it("leaves the default tab out of the URL", () => {
    const { result } = setup({ tab: "history" })

    act(() => result.current[1]("overview"))

    expect(writtenSearch()).toMatchObject({ tab: undefined })
  })

  it("does not stack an entry for the tab already open", () => {
    const { result } = setup({ tab: "feedback" })

    act(() => result.current[1]("feedback"))

    expect(navigate).not.toHaveBeenCalled()
  })

  it("reads the active tab from the URL and falls back to the default", () => {
    expect(setup({ tab: "history" }).result.current[0]).toBe("history")
    expect(setup({ tab: "nonsense" }).result.current[0]).toBe("overview")
    expect(setup().result.current[0]).toBe("overview")
  })

  it("keeps the rest of the search params when it writes the tab", () => {
    const { result } = setup({ page: 3, status: "Active" })

    act(() => result.current[1]("history"))

    expect(writtenSearch()).toMatchObject({ page: 3, status: "Active", tab: "history" })
  })
})
