import { describe, expect, it } from "vitest"

import { routeTitle } from "@/components/DashboardHeader"

describe("routeTitle", () => {
  it("uses the explicit title where one is mapped", () => {
    expect(routeTitle("/")).toBe("Home")
    expect(routeTitle("/me")).toBe("Profile")
    expect(routeTitle("/design")).toBe("Design gallery")
  })

  it("humanises a list route", () => {
    expect(routeTitle("/clients")).toBe("Clients")
    expect(routeTitle("/service-sessions")).toBe("Service sessions")
  })

  it("falls back to the section for a detail route rather than showing the id", () => {
    const id = "9f2c4b1e-8a3d-4f77-b21c-5e6a7d8c9b01"
    expect(routeTitle(`/clients/${id}`, { clientId: id })).toBe("Clients")
  })

  it("skips a numeric id just the same", () => {
    expect(routeTitle("/contracts/482", { contractId: "482" })).toBe("Contracts")
  })

  it("skips every param on a nested detail route", () => {
    expect(routeTitle("/clients/abc/contracts/def", { clientId: "abc", contractId: "def" })).toBe(
      "Contracts",
    )
  })

  it("keeps a trailing segment that is not a param", () => {
    expect(routeTitle("/care-callbacks/worklist")).toBe("Worklist")
  })

  it("does not treat a segment as an id just because it looks like one", () => {
    expect(routeTitle("/clients/482")).toBe("482")
  })

  it("returns Home when there is nothing nameable", () => {
    expect(routeTitle("/abc", { id: "abc" })).toBe("Home")
  })
})
