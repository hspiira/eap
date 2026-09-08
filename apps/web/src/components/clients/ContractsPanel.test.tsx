import { screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { contractLabel } from "@/lib/display"
import { renderWithProviders } from "@/test/utils"
import type { Contract } from "@/types/entities"

import { ContractsPanel } from "./ClientDetailWidgets"

const mocks = vi.hoisted(() => ({
  assignments: vi.fn(),
  service: vi.fn(),
  documents: vi.fn(),
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
  } as Contract
}

const EXPIRED = contract("expired-term", "2024-10-01", "2025-09-30", false)
const CURRENT = contract("current-term", "2025-10-01", "2026-09-30", true)

beforeEach(() => {
  vi.clearAllMocks()
  mocks.documents.mockResolvedValue({ items: [], total: 0 })
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

  it("counts the services each term covers without fetching them all", async () => {
    renderWithProviders(
      <ContractsPanel contracts={[EXPIRED, CURRENT]} loading={false} clientId="client-1" />,
    )
    expect(await screen.findByText("14")).toBeInTheDocument()
    expect(mocks.assignments).toHaveBeenCalledWith({ contract_id: CURRENT.id, limit: 1 })
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
