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
import { getStatusColors, getStatusIcon, getStatusLabel } from "@/utils/statusColors"

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

/**
 * Statuses that are genuinely inert, and so are meant to land on grey.
 *
 * Pending joined this list when the tones were aligned to IBM Carbon's status
 * indicator pattern: Carbon separates "In Progress", a process started but not
 * finished, from "Not Started", a job or step that has not begun. Pending is
 * the default a row is created with, so it has not begun.
 */
const INERT = new Set([
  "Archived",
  "Cancelled",
  "Closed",
  "Draft",
  "Expired",
  "Inactive",
  "Pending",
  "Pending Verification",
  "Refunded",
  "ReferredOut",
  "Resigned",
])

describe("getStatusColors", () => {
  it("never puts white text on a light fill (that renders at ~1.09:1 contrast)", () => {
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
        // White is only safe because the neutral fill is a mid grey, never the
        // near-white surface token this once used.
        expect(colors.bg).toBe("bg-status-neutral")
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

  it("separates the four member lifecycle states so a list can be read at a glance", () => {
    expect(getStatusColors(EligibilityStatus.ACTIVE).tone).toBe("success")
    expect(getStatusColors(EligibilityStatus.PENDING).tone).toBe("neutral")
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

  it("Closed sits on the grey status chip, not on a near-white surface", () => {
    expect(getStatusColors("Closed")).toEqual({
      tone: "neutral",
      bg: "bg-status-neutral",
      text: "text-white",
      border: "border-status-neutral",
    })
  })

  it("unmapped statuses land on the neutral fill rather than white-on-white", () => {
    const colors = getStatusColors("SomeUnmappedFutureStatus")
    expect(colors.tone).toBe("neutral")
    expect(colors.bg).toBe("bg-status-neutral")
  })
})

/**
 * Tone assignment follows IBM Carbon's status indicator pattern, the closest
 * published standard to a status badge.
 */
describe("tones follow the published standard", () => {
  it("treats pending as not started, not as in flight", () => {
    expect(getStatusColors("Pending").tone).toBe("neutral")
    expect(getStatusColors("PendingVerification").tone).toBe("neutral")
  })

  it("keeps blue for work that is actually under way", () => {
    for (const status of ["InProgress", "Processing", "Scheduled", "ToBeContinued"]) {
      expect(getStatusColors(status).tone, status).toBe("info")
    }
  })

  it("treats a refusal as danger rather than a recoverable warning", () => {
    expect(getStatusColors("Declined").tone).toBe("danger")
    expect(getStatusColors("Rejected").tone).toBe("danger")
  })

  it("keeps recoverable pauses as warnings", () => {
    for (const status of ["Suspended", "OnLeave", "Lapsed"]) {
      expect(getStatusColors(status).tone, status).toBe("warning")
    }
  })
})

/**
 * Both themes use the solid role colour. The dark palette makes each role a
 * light colour, so the foreground flips through the `bg` token rather than the
 * fill dropping to a tinted `-soft` variant, which is what made dark mode look
 * glassy.
 */
describe("both themes use the solid role colour", () => {
  it("fills with the role colour, with no soft tint and no dark-mode variant", () => {
    for (const status of ["Active", "Pending", "Declined", "Suspended", "InProgress"]) {
      const { bg } = getStatusColors(status)
      expect(bg, status).not.toMatch(/-soft/)
      expect(bg, status).not.toMatch(/dark:/)
    }
  })

  it("puts white on every fill, because every fill is deep in both themes", () => {
    for (const status of ["Active", "Pending", "Declined", "Suspended", "InProgress"]) {
      expect(getStatusColors(status).text, status).toBe("text-white")
    }
  })
})

/**
 * In an icon-only column the shape is what separates two statuses of the same
 * tone. Keying icons on tone alone left every neutral status identical.
 */
describe("icons distinguish statuses within a tone", () => {
  it("gives each neutral status its own icon", () => {
    const names = ["Pending", "Inactive", "Archived", "Deleted", "Cancelled", "Draft"]
    const icons = names.map((n) => getStatusIcon(n))
    expect(new Set(icons).size).toBe(names.length)
  })

  it("separates two success statuses that share a tone", () => {
    expect(getStatusColors("Active").tone).toBe(getStatusColors("Approved").tone)
    expect(getStatusIcon("Active")).not.toBe(getStatusIcon("Approved"))
  })

  it("falls back to the tone icon for a status with no icon of its own", () => {
    expect(getStatusIcon("SomethingNobodyMapped")).toBe(getStatusIcon("Unmapped2"))
  })
})

describe("labels are unchanged", () => {
  it("splits wire values on the case boundary and keeps acronyms", () => {
    expect(getStatusLabel("InProgress")).toBe("In Progress")
    expect(getStatusLabel("CISMResponse")).toBe("CISM Response")
  })
})
