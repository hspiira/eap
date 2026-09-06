/**
 * The completion dialog is the only place in the product that can trigger
 * entitlement drawdown. The API has accepted `case_id` since the drawdown
 * work landed, but nothing sent it, so drawdown never fired. These tests pin
 * that the case reaches the API and that the picker stays behind clinical
 * scope.
 */

import { screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"
import { CaseStatus, PresentingProblem } from "@/types/enums"

const mocks = vi.hoisted(() => ({
  listCases: vi.fn(),
  hasScope: true,
}))

vi.mock("@/api/endpoints/cases", () => ({ casesApi: { list: mocks.listCases } }))
vi.mock("@/hooks/useCanWrite", async (importOriginal) => ({
  ...(await importOriginal<Record<string, unknown>>()),
  useHasClinicalScope: () => ({ hasScope: mocks.hasScope, isLoading: false }),
}))

const { CompleteDialog } = await import("@/components/sessions/SessionDetailWidgets")

function makeCase(overrides: Record<string, unknown> = {}) {
  return {
    id: "case-1",
    tenant_id: "t1",
    clinical_subject_id: "subject-aaa",
    client_id: "client-1",
    presenting_problem: PresentingProblem.STRESS,
    referral_source: "SelfReferral",
    status: CaseStatus.ACTIVE,
    opened_at: "2026-01-01T00:00:00Z",
    intake_screener_admin_ids: [],
    closure_screener_admin_ids: [],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.hasScope = true
  mocks.listCases.mockResolvedValue([makeCase()])
})

async function fillRequiredFields(user: ReturnType<typeof userEvent.setup>) {
  // The required marker is inside the label, so match on the control id.
  const duration = document.querySelector("#complete-duration") as HTMLInputElement
  const notes = document.querySelector("#complete-notes") as HTMLTextAreaElement
  await user.clear(duration)
  await user.type(duration, "45")
  await user.type(notes, "Attended")
}

describe("CompleteDialog drawdown", () => {
  it("sends the chosen case so the session draws down", async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn().mockResolvedValue(undefined)
    renderWithProviders(
      <CompleteDialog
        open
        onOpenChange={vi.fn()}
        defaultDuration={60}
        clientId="client-1"
        onConfirm={onConfirm}
      />,
    )
    await fillRequiredFields(user)

    await user.click(await screen.findByRole("combobox", { name: "Draw down against case" }))
    await user.click(await screen.findByRole("option", { name: /subject-aaa/ }))
    await user.click(screen.getByRole("button", { name: "Complete session" }))

    await waitFor(() => expect(onConfirm).toHaveBeenCalledWith(45, "Attended", "case-1"))
  })

  it("leaves the authorization alone when no case is chosen", async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn().mockResolvedValue(undefined)
    renderWithProviders(
      <CompleteDialog open onOpenChange={vi.fn()} defaultDuration={60} onConfirm={onConfirm} />,
    )
    await fillRequiredFields(user)

    await user.click(screen.getByRole("button", { name: "Complete session" }))

    await waitFor(() => expect(onConfirm).toHaveBeenCalledWith(45, "Attended", undefined))
  })

  it("does not offer or fetch cases without clinical scope", async () => {
    mocks.hasScope = false
    renderWithProviders(
      <CompleteDialog open onOpenChange={vi.fn()} defaultDuration={60} onConfirm={vi.fn()} />,
    )

    await waitFor(() => expect(document.querySelector("#complete-notes")).not.toBeNull())
    expect(
      screen.queryByRole("combobox", { name: "Draw down against case" }),
    ).not.toBeInTheDocument()
    expect(mocks.listCases).not.toHaveBeenCalled()
  })

  it("offers only live cases for this client", async () => {
    mocks.listCases.mockResolvedValue([
      makeCase(),
      makeCase({
        id: "case-closed",
        clinical_subject_id: "subject-closed",
        status: CaseStatus.CLOSED,
      }),
      makeCase({
        id: "case-referred",
        clinical_subject_id: "subject-referred",
        status: CaseStatus.REFERRED_OUT,
      }),
      makeCase({
        id: "case-other",
        clinical_subject_id: "subject-other",
        client_id: "client-2",
      }),
    ])
    const user = userEvent.setup()
    renderWithProviders(
      <CompleteDialog
        open
        onOpenChange={vi.fn()}
        defaultDuration={60}
        clientId="client-1"
        onConfirm={vi.fn()}
      />,
    )

    await user.click(await screen.findByRole("combobox", { name: "Draw down against case" }))
    const options = within(await screen.findByRole("listbox"))

    expect(options.getByRole("option", { name: /subject-aaa/ })).toBeInTheDocument()
    expect(options.queryByRole("option", { name: /subject-closed/ })).not.toBeInTheDocument()
    expect(options.queryByRole("option", { name: /subject-referred/ })).not.toBeInTheDocument()
    expect(options.queryByRole("option", { name: /subject-other/ })).not.toBeInTheDocument()
  })
})
