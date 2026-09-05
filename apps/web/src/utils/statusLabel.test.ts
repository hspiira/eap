import { describe, expect, it } from "vitest"

import * as enums from "@/types/enums"
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

  /**
   * Two assertions over every PascalCase value in every enum, one for each
   * failure mode this helper has shipped.
   *
   * Reversibility, that removing the spaces gives back the wire value, catches
   * an acronym flattened by lower-casing the tail: Cismresponse does not give
   * back CISMResponse. On its own it misses words left glued together, because
   * a helper that returns its input unchanged round-trips perfectly.
   *
   * The case-boundary check catches that second mode. The narrower versions
   * above cover only PersonType and ServiceCategory, so this is what guards a
   * new member of any other enum without anyone adding a case.
   */
  it("round-trips every PascalCase value in every enum", () => {
    const pascal = /^[A-Z][A-Za-z0-9]*$/
    const values = (Object.values(enums) as unknown[])
      .filter((e) => typeof e === "object" && e !== null)
      .flatMap((e) => Object.values(e as Record<string, unknown>))
      .filter((v): v is string => typeof v === "string" && pascal.test(v))

    expect(values.length).toBeGreaterThan(200)
    for (const value of values) {
      const label = getStatusLabel(value)
      expect(label.replace(/ /g, ""), `${value} did not survive labelling`).toBe(value)
      expect(label, `${value} was left glued`).not.toMatch(/[a-z][A-Z]/)
    }
  })
})
