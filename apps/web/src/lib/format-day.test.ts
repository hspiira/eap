import { describe, expect, it } from "vitest"

import { addDaysToDay, addYearsToDay, daysBetweenDays, formatDay, toDayKey } from "@/lib/format"

describe("toDayKey", () => {
  it("reads the day out of a UTC-midnight instant without shifting it", () => {
    expect(toDayKey("2026-03-31T00:00:00Z")).toBe("2026-03-31")
  })

  it("reads a date-only string as itself", () => {
    expect(toDayKey("2026-03-31")).toBe("2026-03-31")
  })

  it("ignores the time of day entirely", () => {
    expect(toDayKey("2026-03-31T23:59:59.999Z")).toBe("2026-03-31")
    expect(toDayKey("2026-03-31T00:00:00+14:00")).toBe("2026-03-31")
  })

  it("returns an empty string for nothing usable", () => {
    expect(toDayKey(null)).toBe("")
    expect(toDayKey(undefined)).toBe("")
    expect(toDayKey("")).toBe("")
    expect(toDayKey("March 2026")).toBe("")
  })
})

describe("formatDay", () => {
  it("formats the day the wire named, not the day the viewer is on", () => {
    expect(formatDay("2026-03-31T00:00:00Z")).toBe(new Date(2026, 2, 31).toLocaleDateString())
  })

  it("returns the placeholder for nothing usable", () => {
    expect(formatDay(null)).toBe("-")
    expect(formatDay("nope")).toBe("-")
  })
})

describe("daysBetweenDays", () => {
  it("counts whole days forward", () => {
    expect(daysBetweenDays("2026-03-01", "2026-03-31")).toBe(30)
  })

  it("counts backward as negative", () => {
    expect(daysBetweenDays("2026-03-31", "2026-03-01")).toBe(-30)
  })

  it("is zero for the same day", () => {
    expect(daysBetweenDays("2026-03-31T00:00:00Z", "2026-03-31")).toBe(0)
  })

  it("crosses a spring DST boundary without losing a day", () => {
    expect(daysBetweenDays("2026-03-07", "2026-03-09")).toBe(2)
  })

  it("crosses a leap day", () => {
    expect(daysBetweenDays("2028-02-28", "2028-03-01")).toBe(2)
  })

  it("is null when either side is unusable", () => {
    expect(daysBetweenDays(null, "2026-03-31")).toBeNull()
    expect(daysBetweenDays("2026-03-31", "nope")).toBeNull()
  })
})

describe("addYearsToDay", () => {
  it("keeps the same calendar day a year on", () => {
    expect(addYearsToDay("2026-03-31T00:00:00Z", 1)).toBe("2027-03-31")
  })

  it("does not drift for a day that would move under local-time arithmetic", () => {
    expect(addYearsToDay("2026-01-01T00:00:00Z", 1)).toBe("2027-01-01")
    expect(addYearsToDay("2026-12-31T00:00:00Z", 1)).toBe("2027-12-31")
  })

  it("rolls 29 February into March when the target year is not a leap year", () => {
    expect(addYearsToDay("2028-02-29", 1)).toBe("2029-03-01")
  })

  it("returns an empty string for nothing usable", () => {
    expect(addYearsToDay(null, 1)).toBe("")
  })
})

describe("addDaysToDay", () => {
  it("shifts a calendar day forward", () => {
    expect(addDaysToDay("2026-03-31", 90)).toBe("2026-06-29")
  })

  it("shifts backward for a negative count", () => {
    expect(addDaysToDay("2026-03-01", -1)).toBe("2026-02-28")
  })

  it("crosses a leap day correctly", () => {
    expect(addDaysToDay("2028-02-28", 1)).toBe("2028-02-29")
    expect(addDaysToDay("2028-02-28", 2)).toBe("2028-03-01")
  })

  it("does not drift across a DST boundary", () => {
    expect(addDaysToDay("2026-03-07", 1)).toBe("2026-03-08")
    expect(addDaysToDay("2026-11-01", 1)).toBe("2026-11-02")
  })

  it("reads a day out of an instant before shifting", () => {
    expect(addDaysToDay("2026-03-31T00:00:00Z", 1)).toBe("2026-04-01")
  })

  it("returns an empty string for nothing usable", () => {
    expect(addDaysToDay(null, 1)).toBe("")
  })
})
