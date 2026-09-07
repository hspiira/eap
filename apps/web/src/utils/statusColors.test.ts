import { describe, expect, it } from "vitest"

import {
  AccreditationStatus,
  CaseStatus,
  ContractStatus,
  EligibilityStatus,
  EngagementStatus,
  IncidentStatus,
  OrganisationApprovalStatus,
  OutreachStatus,
  PanelStatus,
  PaymentStatus,
  SessionStatus,
  TenantStatus,
  UserStatus,
  WorkStatus,
} from "@/types/enums"
import { getStatusColors } from "@/utils/statusColors"

/** The status enums a badge can be handed. Every member must be tone-mapped. */
const STATUS_ENUMS = {
  AccreditationStatus,
  CaseStatus,
  ContractStatus,
  EligibilityStatus,
  EngagementStatus,
  IncidentStatus,
  OrganisationApprovalStatus,
  OutreachStatus,
  PanelStatus,
  PaymentStatus,
  SessionStatus,
  TenantStatus,
  UserStatus,
  WorkStatus,
}

/** Statuses that are genuinely inert, and so are meant to land on grey. */
const INERT = new Set([
  "Archived",
  "Cancelled",
  "Closed",
  "Draft",
  "Expired",
  "Inactive",
  "Refunded",
  "ReferredOut",
  "Resigned",
])

describe("getStatusColors", () => {
  it("never pairs the muted background with white text (that renders at ~1.09:1 contrast)", () => {
    const statuses = [
      "Closed",
      "ReferredOut",
      "Intake",
      "Inactive",
      "Cancelled",
      "Suspended",
      "NoShowClosed",
      "SomeUnmappedFutureStatus",
    ]
    for (const status of statuses) {
      const colors = getStatusColors(status)
      if (colors.tone === "neutral") {
        expect(colors.text).not.toContain("text-white")
      }
    }
  })

  it("gives every status on every badge-bearing enum a tone, not the grey fallback", () => {
    const uncoloured: string[] = []
    for (const [name, statuses] of Object.entries(STATUS_ENUMS)) {
      for (const status of Object.values(statuses)) {
        if (getStatusColors(status).tone === "neutral" && !INERT.has(status)) {
          uncoloured.push(`${name}.${status}`)
        }
      }
    }
    expect(uncoloured).toEqual([])
  })

  it("separates the three member lifecycle states so a list can be read at a glance", () => {
    expect(getStatusColors(EligibilityStatus.ACTIVE).tone).toBe("success")
    expect(getStatusColors(EligibilityStatus.PENDING).tone).toBe("info")
    expect(getStatusColors(EligibilityStatus.SUSPENDED).tone).toBe("warning")
    expect(getStatusColors(EligibilityStatus.TERMINATED).tone).toBe("danger")
  })

  it("Terminated is red, so a member who has lost cover is not read as merely inactive", () => {
    const terminated = getStatusColors("Terminated")
    expect(terminated.tone).toBe("danger")
    expect(terminated.bg).toContain("bg-danger")
  })

  it("matches a status whatever separators the wire uses", () => {
    expect(getStatusColors("In Progress")).toEqual(getStatusColors("InProgress"))
    expect(getStatusColors("in_progress")).toEqual(getStatusColors("InProgress"))
  })

  it("Closed uses dark text on its light muted background", () => {
    expect(getStatusColors("Closed")).toEqual({
      tone: "neutral",
      bg: "bg-muted",
      text: "text-safe-dark",
      border: "border-safe-dark",
    })
  })

  it("unmapped statuses (the default bucket) use dark text, not white-on-white", () => {
    const colors = getStatusColors("SomeUnmappedFutureStatus")
    expect(colors.tone).toBe("neutral")
    expect(colors.text).toBe("text-safe-dark")
  })
})
