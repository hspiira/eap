/**
 * The alias review queue.
 *
 * Four legacy mappings were loaded as `inferred` so the import could proceed,
 * on the understanding that a clinical owner would check them. I added the API
 * for that and nearly shipped it with no caller, which is the same mistake the
 * drawdown work had made: "listable for review" means nothing if reviewing
 * requires SQL.
 */

import { screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({
  listAliases: vi.fn(),
  upsertAlias: vi.fn(),
}))

vi.mock("@/api/endpoints/diagnoses", () => ({
  diagnosesApi: { listAliases: mocks.listAliases, upsertAlias: mocks.upsertAlias },
}))

const { AliasReviewPanel } = await import("@/components/diagnoses/AliasReviewPanel")

const TREE = {
  types: [
    {
      id: "type-1",
      code: "BEHAV",
      name: "Behavioural / Personality",
      description: null,
      sort_order: 0,
      diagnoses: [
        {
          id: "dx-1",
          code: "PERS",
          name: "Personality issues",
          type_id: "type-1",
          sort_order: 0,
        },
      ],
    },
  ],
}

function alias(overrides: Record<string, unknown> = {}) {
  return {
    id: "dxa_inf_0000",
    raw_value: "Personality",
    normalised_key: "personality",
    diagnosis_type_id: "type-1",
    diagnosis_id: "dx-1",
    source: "inferred_review_2026_09",
    confidence: "inferred",
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.listAliases.mockResolvedValue([alias()])
  mocks.upsertAlias.mockResolvedValue(alias({ confidence: "confirmed" }))
})

describe("AliasReviewPanel", () => {
  it("asks only for the mappings awaiting review", async () => {
    renderWithProviders(<AliasReviewPanel tree={TREE} />)
    await waitFor(() => expect(mocks.listAliases).toHaveBeenCalledWith("inferred"))
  })

  it("shows the legacy spelling and the taxonomy row it resolves to", async () => {
    renderWithProviders(<AliasReviewPanel tree={TREE} />)

    expect(await screen.findByText("Personality")).toBeInTheDocument()
    expect(screen.getByText("Behavioural / Personality / Personality issues")).toBeInTheDocument()
  })

  it("falls back to the type when the mapping names no leaf", async () => {
    mocks.listAliases.mockResolvedValue([alias({ diagnosis_id: null })])
    renderWithProviders(<AliasReviewPanel tree={TREE} />)

    expect(await screen.findByText("Behavioural / Personality")).toBeInTheDocument()
  })

  it("confirming keeps the mapping and only changes the confidence", async () => {
    // Confirming must not silently re-point the alias somewhere else.
    const user = userEvent.setup()
    renderWithProviders(<AliasReviewPanel tree={TREE} />)
    await user.click(await screen.findByRole("button", { name: /confirm/i }))

    await waitFor(() =>
      expect(mocks.upsertAlias).toHaveBeenCalledWith({
        raw_value: "Personality",
        diagnosis_type_id: "type-1",
        diagnosis_id: "dx-1",
        source: "inferred_review_2026_09",
        confidence: "confirmed",
      }),
    )
  })

  it("rejecting records the refusal instead of deleting the mapping", async () => {
    const user = userEvent.setup()
    renderWithProviders(<AliasReviewPanel tree={TREE} />)
    await user.click(await screen.findByRole("button", { name: /reject/i }))

    await waitFor(() =>
      expect(mocks.upsertAlias).toHaveBeenCalledWith({
        raw_value: "Personality",
        diagnosis_type_id: "type-1",
        diagnosis_id: "dx-1",
        source: "inferred_review_2026_09",
        confidence: "rejected",
      }),
    )
  })

  it("offers both decisions on every queued mapping", async () => {
    renderWithProviders(<AliasReviewPanel tree={TREE} />)
    expect(await screen.findByRole("button", { name: /confirm/i })).toBeEnabled()
    expect(screen.getByRole("button", { name: /reject/i })).toBeEnabled()
  })

  it("drops a row from the queue once it is confirmed", async () => {
    const user = userEvent.setup()
    mocks.listAliases.mockResolvedValueOnce([alias()]).mockResolvedValueOnce([])
    renderWithProviders(<AliasReviewPanel tree={TREE} />)
    await user.click(await screen.findByRole("button", { name: /confirm/i }))

    await waitFor(() => expect(screen.queryByText("Personality")).not.toBeInTheDocument())
  })

  it("renders nothing when the queue is empty", async () => {
    mocks.listAliases.mockResolvedValue([])
    const { container } = renderWithProviders(<AliasReviewPanel tree={TREE} />)

    await waitFor(() => expect(mocks.listAliases).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })

  it("counts the queue so the work is visible before scrolling", async () => {
    mocks.listAliases.mockResolvedValue([
      alias(),
      alias({ id: "b", raw_value: "Change Magement Risks" }),
    ])
    renderWithProviders(<AliasReviewPanel tree={TREE} />)

    const heading = await screen.findByRole("heading", { level: 2 })
    expect(within(heading).getByText(/2 legacy spellings awaiting review/i)).toBeInTheDocument()
  })

  it("reports a failed confirmation instead of looking like it worked", async () => {
    // The server's own message is shown when there is one, so the reviewer
    // sees why rather than a generic failure.
    const user = userEvent.setup()
    mocks.upsertAlias.mockRejectedValue(new Error("Diagnosis does not belong to the given type"))
    renderWithProviders(<AliasReviewPanel tree={TREE} />)
    await user.click(await screen.findByRole("button", { name: /confirm/i }))

    expect(
      await screen.findByText(/diagnosis does not belong to the given type/i),
    ).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument()
  })

  it("falls back to a plain message when the failure carries none", async () => {
    const user = userEvent.setup()
    mocks.upsertAlias.mockRejectedValue({})
    renderWithProviders(<AliasReviewPanel tree={TREE} />)
    await user.click(await screen.findByRole("button", { name: /confirm/i }))

    expect(await screen.findByText(/could not confirm this mapping/i)).toBeInTheDocument()
  })
})
