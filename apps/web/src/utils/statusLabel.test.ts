import { describe, expect, it } from "vitest"

import { PersonType, ServiceCategory } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

describe("getStatusLabel over real enum values", () => {
  it("splits every PersonType value into words", () => {
    expect(getStatusLabel(PersonType.CLIENT_EMPLOYEE)).toBe("Client Employee")
    for (const value of Object.values(PersonType)) {
      expect(getStatusLabel(value)).not.toMatch(/[a-z][A-Z]/)
    }
  })

  it("splits every ServiceCategory value into words", () => {
    for (const value of Object.values(ServiceCategory)) {
      expect(getStatusLabel(value)).not.toMatch(/[a-z][A-Z]/)
    }
  })

  it("leaves a single-word value alone", () => {
    expect(getStatusLabel("Active")).toBe("Active")
    expect(getStatusLabel("Paid")).toBe("Paid")
  })

  it("passes through a value that already contains spaces", () => {
    expect(getStatusLabel("Already Spaced")).toBe("Already Spaced")
  })

  it("mangles an embedded acronym, which is a known limit", () => {
    // Documents current behaviour so a future fix has a failing case to flip.
    // CaseReferralSource and ClinicalNoteType carry CISM values; if either is
    // ever rendered through this helper the acronym is lost.
    expect(getStatusLabel("CISMFollowUp")).toBe("Cismfollow Up")
  })
})
