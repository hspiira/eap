import { describe, expect, it } from "vitest"

import { surveysApi } from "@/api/endpoints/surveys"
import { SURVEY_K_FLOOR } from "@/api/endpoints/surveys-fixture"
import { SurveyCampaignStatus, SurveySource } from "@/types/enums"

describe("surveysApi (fixture mode)", () => {
  it("lists seeded surveys in the API's envelope, most-recent first", async () => {
    const r = await surveysApi.list()
    expect(r.items.length).toBeGreaterThanOrEqual(2)
    expect(r.total).toBeGreaterThanOrEqual(r.items.length)
    expect(r.page).toBe(1)
    expect(typeof r.has_more).toBe("boolean")
  })

  it("pages, and page two is a different slice with the same total", async () => {
    const first = await surveysApi.list({ page: 1, limit: 1 })
    const second = await surveysApi.list({ page: 2, limit: 1 })
    expect(first.has_more).toBe(true)
    expect(second.items[0].id).not.toBe(first.items[0].id)
    expect(second.total).toBe(first.total)
  })

  it("filters server-side, so the total is the filtered total", async () => {
    const all = await surveysApi.list({ limit: 100 })
    const drafts = await surveysApi.list({ status: SurveyCampaignStatus.DRAFT, limit: 100 })
    expect(drafts.total).toBeLessThan(all.total)
    expect(drafts.items.every((s) => s.status === SurveyCampaignStatus.DRAFT)).toBe(true)
  })

  it("aggregate exposes metrics when k-floor met (srv-001)", async () => {
    const agg = await surveysApi.getAggregate("srv-001")
    expect(agg.response_count).toBeGreaterThanOrEqual(SURVEY_K_FLOOR)
    expect(agg.k_floor_met).toBe(true)
    expect(agg.satisfaction_mean).not.toBeNull()
    expect(agg.nps).not.toBeNull()
  })

  it("aggregate suppresses metrics when k-floor unmet (srv-002)", async () => {
    const agg = await surveysApi.getAggregate("srv-002")
    expect(agg.response_count).toBeLessThan(SURVEY_K_FLOOR)
    expect(agg.k_floor_met).toBe(false)
    expect(agg.satisfaction_mean).toBeNull()
    expect(agg.nps).toBeNull()
    for (const s of agg.question_summaries) {
      expect(s.mean).toBeNull()
      expect(s.histogram).toBeNull()
    }
  })

  it("create drafts a survey and never echoes the webhook secret", async () => {
    const created = await surveysApi.create({
      client_id: "client-x",
      name: "New survey",
      source: SurveySource.GOOGLE_FORMS,
      external_form_id: "form-x",
      webhook_secret: "s".repeat(48),
      anonymous: true,
      period_start: "2026-06-01",
      period_end: "2026-06-30",
    })
    expect(created.status).toBe(SurveyCampaignStatus.DRAFT)
    expect(created.external_form_id).toBe("form-x")
    expect(created).not.toHaveProperty("webhook_secret")
  })

  it("activate transitions a DRAFT survey to ACTIVE", async () => {
    const created = await surveysApi.create({
      client_id: "client-x",
      name: "Activation test",
      source: SurveySource.GOOGLE_FORMS,
      external_form_id: "form-y",
      webhook_secret: "s".repeat(48),
      anonymous: true,
      period_start: "2026-06-01",
      period_end: "2026-06-30",
    })
    expect(created.status).toBe(SurveyCampaignStatus.DRAFT)
    const activated = await surveysApi.activate(created.id)
    expect(activated.status).toBe(SurveyCampaignStatus.ACTIVE)
    expect(activated.activated_at).not.toBeNull()
  })

  it("close transitions the survey to CLOSED", async () => {
    const closed = await surveysApi.close("srv-002")
    expect(closed.status).toBe(SurveyCampaignStatus.CLOSED)
    expect(closed.closed_at).not.toBeNull()
  })
})
