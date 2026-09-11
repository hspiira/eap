import { describe, expect, it } from "vitest"

import { applyPace } from "./apply-progress"

const START = 1_000_000

describe("applyPace", () => {
  it("withholds an estimate until enough rows have been written to measure one", () => {
    const pace = applyPace(3, 1000, START, START + 2_000)
    expect(pace.rate).toBeNull()
    expect(pace.eta).toBeNull()
    expect(pace.percent).toBe(0)
  })

  it("measures the rate from what this run actually wrote", () => {
    // 100 rows in 10 seconds.
    const pace = applyPace(100, 1000, START, START + 10_000)
    expect(pace.rate).toBe(10)
    // 900 left at 10/s is 90 seconds.
    expect(pace.eta).toBe("about 2 min left")
  })

  it("says under a minute rather than a misleading count of seconds", () => {
    const pace = applyPace(100, 120, START, START + 10_000)
    expect(pace.eta).toBe("under a minute left")
  })

  it("spells out hours for a long roster", () => {
    // 10 rows in 10 seconds is 1/s; 5400 left is an hour and a half.
    const pace = applyPace(10, 5410, START, START + 10_000)
    expect(pace.eta).toBe("about 1 h 30 min left")
  })

  it("has no estimate left to give once everything is written", () => {
    const pace = applyPace(500, 500, START, START + 50_000)
    expect(pace.percent).toBe(100)
    expect(pace.eta).toBeNull()
  })

  it("never reports more than complete", () => {
    const pace = applyPace(600, 500, START, START + 50_000)
    expect(pace.percent).toBe(100)
  })

  it("treats an empty batch as finished rather than dividing by zero", () => {
    const pace = applyPace(0, 0, START, START + 1_000)
    expect(pace.percent).toBe(100)
    expect(pace.eta).toBeNull()
  })

  it("withholds an estimate when no time has passed", () => {
    const pace = applyPace(50, 500, START, START)
    expect(pace.rate).toBeNull()
  })
})
