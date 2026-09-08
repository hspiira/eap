import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"
import type { Contract } from "@/types/entities"

import { ClientDocumentsPanel, ClientUtilisationPanel } from "./ClientManagementPanels"
import { ContractServicesCard } from "./ContractServicesCard"

const mocks = vi.hoisted(() => ({
  contracts: vi.fn(),
  assignments: vi.fn(),
  service: vi.fn(),
  documents: vi.fn(),
  usage: vi.fn(),
}))
vi.mock("@/api/endpoints/contracts", () => ({ contractsApi: { list: mocks.contracts } }))
vi.mock("@/api/endpoints/service-assignments", () => ({
  serviceAssignmentsApi: { list: mocks.assignments },
}))
vi.mock("@/api/endpoints/services", () => ({ servicesApi: { getById: mocks.service } }))
vi.mock("@/api/endpoints/documents", () => ({ documentsApi: { list: mocks.documents } }))
vi.mock("@/api/endpoints/utilisation", () => ({ utilisationApi: { byContract: mocks.usage } }))
vi.mock("@tanstack/react-router", () => ({
  Link: ({
    children,
    params,
    to,
  }: {
    children: React.ReactNode
    params: Record<string, string>
    to: string
  }) => <a href={to.replace(/\$(\w+)/g, (_, key: string) => params[key])}>{children}</a>,
}))

const contract = {
  id: "private-contract-id",
  status: "Active",
  period: { start_date: "2026-01-01", end_date: "2026-12-31" },
} as Contract
beforeEach(() => {
  vi.clearAllMocks()
  mocks.contracts.mockResolvedValue({ items: [contract], total: 1 })
  mocks.assignments.mockResolvedValue({
    items: [{ id: "assignment-1", service_id: "private-service-id", status: "Active" }],
    total: 1,
  })
  mocks.documents.mockResolvedValue({ items: [], total: 0 })
  mocks.service.mockResolvedValue({
    id: "private-service-id",
    name: "Counselling",
    category: "Therapy",
    status: "Active",
  })
})

describe("client detail tab records", () => {
  it("lists a contract's services with their assignment notes, resolving each service once", async () => {
    mocks.assignments.mockResolvedValue({
      items: [
        {
          id: "assignment-1",
          service_id: "private-service-id",
          status: "Active",
          notes: "Six sessions per employee per year.",
        },
        { id: "assignment-2", service_id: "private-service-id", status: "Inactive" },
      ],
      total: 2,
    })
    renderWithProviders(<ContractServicesCard contract={contract} onClose={() => {}} />)
    expect((await screen.findAllByRole("link", { name: "Counselling" }))[0]).toHaveAttribute(
      "href",
      "/services/private-service-id",
    )
    expect(screen.getByText("Six sessions per employee per year.")).toBeInTheDocument()
    expect(mocks.service).toHaveBeenCalledTimes(1)
    expect(screen.queryByText("private-service-id")).not.toBeInTheDocument()
    expect(screen.queryByText("Therapy")).not.toBeInTheDocument()
  })

  it("shows failed document requests as errors and retries them", async () => {
    mocks.documents.mockRejectedValue(new Error("Documents unavailable"))
    const user = userEvent.setup()
    renderWithProviders(<ClientDocumentsPanel clientId="client-1" />)
    expect(await screen.findByRole("alert")).toHaveTextContent("Documents unavailable")
    expect(screen.queryByText("No documents linked yet.")).not.toBeInTheDocument()
    mocks.documents.mockResolvedValue({ items: [], total: 0 })
    await user.click(screen.getByRole("button", { name: "Retry" }))
    expect(await screen.findByText("No documents linked yet.")).toBeInTheDocument()
  })

  it("shows usage by readable contract terms without internal identifiers", async () => {
    mocks.usage.mockResolvedValue([
      {
        id: "event-1",
        occurred_on: "2026-09-05",
        units: 3,
        event_type: "ServiceDelivered",
        service_code: "private-service-id",
      },
    ])
    renderWithProviders(<ClientUtilisationPanel clientId="client-1" />)
    expect(await screen.findByRole("link")).toHaveAttribute(
      "href",
      "/contracts/private-contract-id",
    )
    expect(screen.getByText("Service Delivered")).toBeInTheDocument()
    expect(screen.queryByText("private-service-id")).not.toBeInTheDocument()
    expect(screen.queryByText("private-contract-id")).not.toBeInTheDocument()
  })
})
