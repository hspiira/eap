import { screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { contractLabel } from "@/lib/display"
import { renderWithProviders } from "@/test/utils"
import type { Contract } from "@/types/entities"

import { ContractsPanel } from "./ClientDetailWidgets"

const mocks = vi.hoisted(() => ({
  metrics: vi.fn(),
  assignments: vi.fn(),
  service: vi.fn(),
  documents: vi.fn(),
}))
vi.mock("@/api/endpoints/contracts", () => ({
  contractsApi: { metricsByClient: mocks.metrics },
}))
vi.mock("@/api/endpoints/service-assignments", () => ({
  serviceAssignmentsApi: { list: mocks.assignments },
}))
vi.mock("@/api/endpoints/services", () => ({ servicesApi: { getById: mocks.service } }))
vi.mock("@/api/endpoints/documents", () => ({ documentsApi: { list: mocks.documents } }))
vi.mock("@tanstack/react-router", () => ({
  Link: ({
    children,
    params,
    to,
  }: {
    children: React.ReactNode
    params?: Record<string, string>
    to: string
  }) => <a href={to.replace(/\$(\w+)/g, (_, key: string) => params?.[key] ?? key)}>{children}</a>,
}))

function contract(id: string, start: string, end: string, isActive: boolean): Contract {
  return {
    id,
    status: isActive ? "Active" : "Expired",
    is_active: isActive,
    period: { start_date: start, end_date: end },
    billing_rate: { amount: "172000000", currency: "UGX" },
  } as Contract
}

function metrics(contractId: string, services: number, sessions: number, amount: string) {
  return {
    contract_id: contractId,
    services,
    sessions,
    sessions_priced: sessions,
    spent: { amount, currency: "UGX" },
  }
}

const EXPIRED = contract("expired-term", "2024-10-01", "2025-09-30", false)
const CURRENT = contract("current-term", "2025-10-01", "2026-09-30", true)

beforeEach(() => {
  vi.clearAllMocks()
  mocks.documents.mockResolvedValue({ items: [], total: 0 })
  mocks.metrics.mockResolvedValue({
    client_id: "client-1",
    items: [metrics(CURRENT.id, 14, 20, "7200000"), metrics(EXPIRED.id, 10, 39, "4660000")],
  })
  mocks.service.mockImplementation(async (id: string) => ({
    id,
    name: id === "counselling-id" ? "Counselling" : "Health Talk",
    status: "Active",
  }))
  mocks.assignments.mockImplementation(
    async ({ contract_id, limit }: { contract_id: string; limit?: number }) => ({
      items: [
        {
          id: `${contract_id}-assignment`,
          contract_id,
          service_id: contract_id === CURRENT.id ? "counselling-id" : "health-talk-id",
          status: "Active",
        },
      ],
      // The count column asks for one row and reads the total off it.
      total: limit === 1 && contract_id === CURRENT.id ? 14 : 1,
    }),
  )
})

describe("contracts panel", () => {
  it("opens on the term in force, whatever order the rows are in", async () => {
    renderWithProviders(
      <ContractsPanel contracts={[EXPIRED, CURRENT]} loading={false} clientId="client-1" />,
    )
    expect(await screen.findByRole("link", { name: "Counselling" })).toBeInTheDocument()
    expect(screen.queryByRole("link", { name: "Health Talk" })).not.toBeInTheDocument()
  })

  it("shows each term's services, value and spend from one metrics request", async () => {
    renderWithProviders(
      <ContractsPanel contracts={[EXPIRED, CURRENT]} loading={false} clientId="client-1" />,
    )
    expect(await screen.findByText("14")).toBeInTheDocument()
    expect(screen.getByText("10")).toBeInTheDocument()
    expect(screen.getByText("UGX 7,200,000")).toBeInTheDocument()
    expect(screen.getByText("UGX 4,660,000")).toBeInTheDocument()
    expect(screen.getAllByText("UGX 172,000,000")).toHaveLength(2)
    expect(mocks.metrics).toHaveBeenCalledTimes(1)
    expect(mocks.metrics).toHaveBeenCalledWith("client-1")
  })

  it("says how much of the spend is priced, since a session can carry no rate", async () => {
    mocks.metrics.mockResolvedValue({
      client_id: "client-1",
      items: [
        { ...metrics(CURRENT.id, 14, 20, "7200000"), sessions_priced: 18 },
        metrics(EXPIRED.id, 10, 0, "0"),
      ],
    })
    renderWithProviders(
      <ContractsPanel contracts={[EXPIRED, CURRENT]} loading={false} clientId="client-1" />,
    )
    expect(await screen.findByTitle("18 of 20 sessions in this term carry a rate")).toBeVisible()
    expect(screen.getByTitle("No sessions recorded in this term")).toBeVisible()
  })

  it("falls back to the top row when no term is in force", async () => {
    renderWithProviders(
      <ContractsPanel contracts={[EXPIRED]} loading={false} clientId="client-1" />,
    )
    expect(await screen.findByRole("link", { name: "Health Talk" })).toBeInTheDocument()
  })

  it("swaps the rail to whichever row is clicked", async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <ContractsPanel contracts={[EXPIRED, CURRENT]} loading={false} clientId="client-1" />,
    )
    await screen.findByRole("link", { name: "Counselling" })
    const expiredRow = screen
      .getAllByRole("row")
      .find((row) => within(row).queryByText(contractLabel(EXPIRED)))
    await user.click(expiredRow!)
    expect(await screen.findByRole("link", { name: "Health Talk" })).toBeInTheDocument()
  })
})
