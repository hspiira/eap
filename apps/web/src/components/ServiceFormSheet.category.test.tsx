import { describe, expect, it } from "vitest"

import { CATEGORY_LABELS } from "@/components/ServiceFormSheet"
import { ServiceCategory } from "@/types/enums"

describe("service category options", () => {
  it("labels every ServiceCategory value", () => {
    for (const value of Object.values(ServiceCategory)) {
      expect(CATEGORY_LABELS[value]).toBeTruthy()
    }
  })

  it("offers only values the API accepts", () => {
    expect(Object.keys(CATEGORY_LABELS).sort()).toEqual(Object.values(ServiceCategory).sort())
  })

  it("does not mangle CISMResponse the way getStatusLabel would", () => {
    expect(CATEGORY_LABELS[ServiceCategory.CISM_RESPONSE]).toBe("CISM response")
  })
})
