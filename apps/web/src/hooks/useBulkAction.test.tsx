import { act, renderHook } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { useBulkAction } from "@/hooks/useBulkAction"
import { TestProviders } from "@/test/utils"

const KEY = ["things"] as const

function setup(options: Partial<Parameters<typeof useBulkAction>[0]> = {}) {
  const action = options.action ?? vi.fn().mockResolvedValue(undefined)
  const onDone = options.onDone ?? vi.fn()
  const view = renderHook(
    () =>
      useBulkAction({
        action,
        invalidateKey: KEY,
        verb: "archived",
        noun: "client",
        ...options,
        onDone,
      }),
    { wrapper: TestProviders },
  )
  return { ...view, action, onDone }
}

describe("useBulkAction", () => {
  it("applies the action once per selected id", async () => {
    const action = vi.fn().mockResolvedValue(undefined)
    const { result } = setup({ action })

    await act(async () => {
      await result.current.run(new Set(["a", "b", "c"]))
    })

    expect(action).toHaveBeenCalledTimes(3)
    expect(action.mock.calls.map((c) => c[0])).toEqual(["a", "b", "c"])
  })

  it("does nothing for an empty selection", async () => {
    const { result, action, onDone } = setup()

    await act(async () => {
      await result.current.run(new Set())
    })

    expect(action).not.toHaveBeenCalled()
    expect(onDone).not.toHaveBeenCalled()
  })

  it("keeps going after a failure so later rows are still attempted", async () => {
    const action = vi
      .fn()
      .mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce(new Error("nope"))
      .mockResolvedValueOnce(undefined)
    const { result } = setup({ action })

    await act(async () => {
      await result.current.run(new Set(["a", "b", "c"]))
    })

    expect(action).toHaveBeenCalledTimes(3)
  })

  it("reports running while the batch is in flight", async () => {
    let release: () => void = () => {}
    const action = vi.fn().mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          release = resolve
        }),
    )
    const { result } = setup({ action })

    let pending: Promise<void>
    await act(async () => {
      pending = result.current.run(new Set(["a"]))
    })
    expect(result.current.running).toBe(true)

    await act(async () => {
      release()
      await pending
    })
    expect(result.current.running).toBe(false)
  })

  it("calls onDone once the batch settles, including when every row failed", async () => {
    const action = vi.fn().mockRejectedValue(new Error("nope"))
    const { result, onDone } = setup({ action })

    await act(async () => {
      await result.current.run(new Set(["a", "b"]))
    })

    expect(onDone).toHaveBeenCalledTimes(1)
  })

  it("resolves labels through labelFor when naming failures", async () => {
    const action = vi.fn().mockResolvedValueOnce(undefined).mockRejectedValueOnce(new Error("nope"))
    const labelFor = vi.fn((id: string) => `Client ${id.toUpperCase()}`)
    const { result } = setup({ action, labelFor })

    await act(async () => {
      await result.current.run(new Set(["a", "b"]))
    })

    expect(labelFor).toHaveBeenCalledWith("b")
  })
})
