import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

import {
  ClientDocumentsPanel,
  ClientServicesPanel,
  ClientUtilisationPanel,
} from "./ClientManagementPanels"

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
}
beforeEach(() => {
  vi.clearAllMocks()
  mocks.contracts.mockResolvedValue({ items: [contract], total: 1 })
  mocks.assignments.mockResolvedValue({
    items: [{ id: "assignment-1", service_id: "private-service-id", status: "Active" }],
    total: 1,
  })
  mocks.service.mockResolvedValue({
    id: "private-service-id",
    name: "Counselling",
    category: "Therapy",
    status: "Active",
  })
})

describe("client detail tab records", () => {
  it("resolves service names and loads contract pages beyond the preview", async () => {
    mocks.contracts.mockImplementation(async ({ page }) => ({
      items: [{ ...contract, id: `contract-${page}` }],
      total: 2,
    }))
    renderWithProviders(<ClientServicesPanel clientId="client-1" />)
    expect((await screen.findAllByRole("link", { name: "Counselling" }))[0]).toHaveAttribute(
      "href",
      "/services/private-service-id",
    )
    expect(mocks.contracts).toHaveBeenCalledTimes(2)
    expect(screen.getAllByRole("article")).toHaveLength(2)
    expect(mocks.service).toHaveBeenCalledTimes(1)
    expect(screen.queryByText("private-service-id")).not.toBeInTheDocument()
    expect(
      screen
        .getAllByRole("link")
        .filter((el) => el.getAttribute("href")?.startsWith("/contracts/")),
    ).toHaveLength(2)
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
