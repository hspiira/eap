/**
 * What each range on the sessions list asks the server for.
 *
 * The bounds are computed in the browser because "today" means the viewer's
 * calendar day, so these pin the edges rather than trusting a timezone.
 */

import { describe, expect, it } from "vitest"

import { rangeBounds } from "./index"

// A Thursday, mid-month, mid-afternoon.
const NOW = new Date(2026, 3, 16, 14, 30)

function local(value: string | undefined) {
  return value ? new Date(value) : null
}

describe("rangeBounds", () => {
  it("asks for nothing at all when the range is all time", () => {
    expect(rangeBounds("all", NOW)).toEqual({})
  })

  it("bounds today to the viewer's own calendar day", () => {
    const { scheduled_from, scheduled_to } = rangeBounds("today", NOW)
    expect(local(scheduled_from)?.getDate()).toBe(16)
    expect(local(scheduled_from)?.getHours()).toBe(0)
    expect(local(scheduled_to)?.getDate()).toBe(16)
    expect(local(scheduled_to)?.getHours()).toBe(23)
  })

  it("runs this week from Monday to Sunday, matching how the API buckets one", () => {
    const { scheduled_from, scheduled_to } = rangeBounds("this_week", NOW)
    // Monday 13 April through Sunday 19 April.
    expect(local(scheduled_from)?.getDay()).toBe(1)
    expect(local(scheduled_from)?.getDate()).toBe(13)
    expect(local(scheduled_to)?.getDay()).toBe(0)
    expect(local(scheduled_to)?.getDate()).toBe(19)
  })

  it("runs this month from the first to the last day, not thirty days out", () => {
    const { scheduled_from, scheduled_to } = rangeBounds("this_month", NOW)
    expect(local(scheduled_from)?.getDate()).toBe(1)
    expect(local(scheduled_from)?.getMonth()).toBe(3)
    expect(local(scheduled_to)?.getDate()).toBe(30)
    expect(local(scheduled_to)?.getMonth()).toBe(3)
  })

  it("ends this month on the right day in February", () => {
    const leap = rangeBounds("this_month", new Date(2028, 1, 10, 9, 0))
    expect(local(leap.scheduled_to)?.getDate()).toBe(29)
  })

  it("rolls the next-N-days ranges forward from this instant", () => {
    const { scheduled_from, scheduled_to } = rangeBounds("7d", NOW)
    expect(local(scheduled_from)?.getTime()).toBe(NOW.getTime())
    expect(local(scheduled_to)?.getDate()).toBe(23)
  })

  it("leaves past sessions open at the beginning", () => {
    const { scheduled_from, scheduled_to } = rangeBounds("past", NOW)
    expect(scheduled_from).toBeUndefined()
    expect(local(scheduled_to)?.getTime()).toBe(NOW.getTime())
  })
})
