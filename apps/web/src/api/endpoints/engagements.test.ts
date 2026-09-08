import { describe, expect, it } from "vitest"

import { engagementsApi } from "@/api/endpoints/engagements"
import { DeliverableStatus, EngagementStatus } from "@/types/enums"

async function createEngagement(name: string) {
  return engagementsApi.create({ client_id: "c-1", name, period_start: "2026-05-01" })
}

describe("engagementsApi (fixture mode)", () => {
  it("lists seeded engagements in the API's envelope", async () => {
    const r = await engagementsApi.list()
    expect(r.items.length).toBeGreaterThanOrEqual(2)
    expect(r.total).toBeGreaterThanOrEqual(r.items.length)
    expect(r.page).toBe(1)
    expect(typeof r.has_more).toBe("boolean")
  })

  it("pages, and page two is a different slice", async () => {
    const first = await engagementsApi.list({ page: 1, limit: 1 })
    const second = await engagementsApi.list({ page: 2, limit: 1 })
    expect(first.items).toHaveLength(1)
    expect(second.items).toHaveLength(1)
    expect(second.items[0].id).not.toBe(first.items[0].id)
    expect(second.total).toBe(first.total)
  })

  it("filters server-side, so the total is the filtered total", async () => {
    const all = await engagementsApi.list({ limit: 100 })
    const drafts = await engagementsApi.list({ status: EngagementStatus.DRAFT, limit: 100 })
    expect(drafts.total).toBeLessThan(all.total)
    expect(drafts.items.every((e) => e.status === EngagementStatus.DRAFT)).toBe(true)
  })

  it("searches by name", async () => {
    const found = await engagementsApi.list({ search: "policy refresh" })
    expect(found.items.map((e) => e.id)).toEqual(["eng-001"])
    expect(found.total).toBe(1)
  })

  it("FSM blocks invalid transitions and allows valid ones", async () => {
    const created = await createEngagement("Smoke FSM")
    expect(created.status).toBe(EngagementStatus.DRAFT)

    await expect(engagementsApi.transition(created.id, EngagementStatus.CLOSED)).rejects.toThrow(
      /Cannot transition/,
    )

    const active = await engagementsApi.transition(created.id, EngagementStatus.ACTIVE)
    expect(active.status).toBe(EngagementStatus.ACTIVE)
    expect(active.activated_at).not.toBeNull()
    const delivered = await engagementsApi.transition(created.id, EngagementStatus.DELIVERED)
    expect(delivered.status).toBe(EngagementStatus.DELIVERED)
    const invoiced = await engagementsApi.transition(created.id, EngagementStatus.INVOICED)
    expect(invoiced.status).toBe(EngagementStatus.INVOICED)
  })

  it("logged hours come back embedded in the engagement, and in its summary", async () => {
    const created = await createEngagement("Hours rollup")
    expect(created.hours_log).toEqual([])

    await engagementsApi.logTime(created.id, {
      user_id: "user-helen",
      logged_on: "2026-05-02",
      hours: 3.5,
    })
    await engagementsApi.logTime(created.id, {
      user_id: "user-mary",
      logged_on: "2026-05-03",
      hours: 2,
    })

    const fresh = await engagementsApi.getById(created.id)
    expect(fresh.hours_log.map((h) => h.hours)).toEqual([3.5, 2])

    const summary = await engagementsApi.getSummary(created.id)
    expect(summary.total_hours).toBeCloseTo(5.5)
    expect(summary.hours_by_user).toEqual({ "user-helen": 3.5, "user-mary": 2 })
  })

  it("deliverables come back embedded, and the summary counts them by status", async () => {
    const created = await createEngagement("Deliverable test")
    const dlv = await engagementsApi.createDeliverable(created.id, { title: "Draft v1" })
    expect(dlv.status).toBe(DeliverableStatus.PENDING)

    const delivered = await engagementsApi.updateDeliverableStatus(
      created.id,
      dlv.id,
      DeliverableStatus.DELIVERED,
    )
    expect(delivered.delivered_at).not.toBeNull()

    const fresh = await engagementsApi.getById(created.id)
    expect(fresh.deliverables.map((d) => d.id)).toEqual([dlv.id])

    const summary = await engagementsApi.getSummary(created.id)
    expect(summary.deliverable_count).toBe(1)
    expect(summary.deliverable_mix).toEqual({ [DeliverableStatus.DELIVERED]: 1 })
  })
})
