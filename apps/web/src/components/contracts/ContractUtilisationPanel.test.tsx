import { screen } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

import { ContractUtilisationPanel } from "./ContractUtilisationPanel"

const mocks = vi.hoisted(() => ({ events: vi.fn(), service: vi.fn() }))
vi.mock("@/api/endpoints/utilisation", () => ({
  utilisationApi: { byContract: mocks.events },
}))
vi.mock("@/api/endpoints/services", () => ({ servicesApi: { getById: mocks.service } }))

const EVENTS = [
  {
    id: "event-1",
    contract_id: "contract-1",
    event_type: "SessionDelivered",
    occurred_on: "2026-08-28",
    units: 2,
    service_code: "private-service-id",
  },
  {
    id: "event-2",
    contract_id: "contract-1",
    event_type: "SessionDelivered",
    occurred_on: "2026-08-20",
    units: 1,
    service_code: "private-service-id",
  },
]

beforeEach(() => {
  vi.clearAllMocks()
  mocks.events.mockResolvedValue(EVENTS)
  mocks.service.mockResolvedValue({ id: "private-service-id", name: "Group Counselling" })
})

describe("contract utilisation panel", () => {
  it("names the service once per code and totals the units", async () => {
    renderWithProviders(<ContractUtilisationPanel contractId="contract-1" />)
    expect(await screen.findByText("2 events · 3 units")).toBeInTheDocument()
    expect(screen.getAllByText("Group Counselling")).toHaveLength(2)
    expect(screen.getAllByText("Session Delivered")).toHaveLength(2)
    expect(mocks.service).toHaveBeenCalledTimes(1)
    expect(screen.queryByText("private-service-id")).not.toBeInTheDocument()
  })

  it("keeps an unresolvable service code off the page", async () => {
    mocks.service.mockRejectedValue(new Error("gone"))
    renderWithProviders(<ContractUtilisationPanel contractId="contract-1" />)
    expect(await screen.findByText("2 events · 3 units")).toBeInTheDocument()
    expect(screen.queryByText("private-service-id")).not.toBeInTheDocument()
  })

  it("says nothing is recorded rather than showing an empty table", async () => {
    mocks.events.mockResolvedValue([])
    renderWithProviders(<ContractUtilisationPanel contractId="contract-1" />)
    expect(
      await screen.findByText("Nothing billable recorded against this term yet."),
    ).toBeInTheDocument()
  })
})
