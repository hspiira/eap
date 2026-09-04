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

  it("keeps an embedded acronym intact", () => {
    expect(getStatusLabel("CISMFollowUp")).toBe("CISM Follow Up")
    // ServiceCategory.CISM_RESPONSE reaches this helper from the service detail page.
    expect(getStatusLabel("CISMResponse")).toBe("CISM Response")
  })

  it("leaves a value that is entirely an acronym alone", () => {
    expect(getStatusLabel("DAP")).toBe("DAP")
    expect(getStatusLabel("SOAP")).toBe("SOAP")
  })
})
