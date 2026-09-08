/**
 * The staged import: nothing is written until a person applies it, and the
 * outcome counts are what tells them whether applying is worth doing.
 */

import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { SessionImportDialog } from "@/components/sessions/SessionImportDialog"
import { renderWithProviders } from "@/test/utils"

const stage = vi.fn()
const apply = vi.fn()
const listRows = vi.fn()

vi.mock("@/api/endpoints/session-imports", () => ({
  sessionImportsApi: {
    stage: (...args: unknown[]) => stage(...args),
    apply: (...args: unknown[]) => apply(...args),
    listRows: (...args: unknown[]) => listRows(...args),
    getBatch: vi.fn(),
    abandon: vi.fn(),
  },
}))

function batch(counts: Record<string, number>) {
  return {
    id: "b_1",
    tenant_id: "t_1",
    source_system: "activity-log",
    file_name: "sessions.csv",
    file_hash: "sha256:abc",
    row_count: 10,
    source_record_key_field: null,
    status: "Staged",
    outcome_counts: counts,
    created_at: "2026-09-07T00:00:00Z",
    applied_at: null,
  }
}

async function stageFile(counts: Record<string, number>) {
  stage.mockResolvedValue(batch(counts))
  listRows.mockResolvedValue({ items: [], total: 0, page: 1, limit: 50 })
  const user = userEvent.setup()
  const screen = renderWithProviders(
    <SessionImportDialog open onOpenChange={() => {}} onImported={() => {}} />,
  )
  const file = new File(["DATE\n2025-09-12\n"], "sessions.csv", { type: "text/csv" })
  await user.type(screen.getByLabelText("Source system"), "activity-log")
  await user.upload(screen.getByLabelText("CSV file"), file)
  await user.click(screen.getByRole("button", { name: /stage file/i }))
  return screen
}

describe("session import", () => {
  it("stages without writing, then offers to apply only the accepted rows", async () => {
    const screen = await stageFile({ Accepted: 3, UnresolvedMember: 7 })
    expect(await screen.findByRole("button", { name: /apply 3 rows/i })).toBeEnabled()
    expect(apply).not.toHaveBeenCalled()
  })

  it("reads the server's enum-prefixed outcome keys", async () => {
    // The batch response has carried both "Accepted" and
    // "ImportRowOutcome.ACCEPTED"; a reader that knows only one shows nothing.
    const screen = await stageFile({ "ImportRowOutcome.ACCEPTED": 4 })
    expect(await screen.findByRole("button", { name: /apply 4 rows/i })).toBeEnabled()
  })

  it("cannot apply a batch with nothing accepted", async () => {
    const screen = await stageFile({ UnresolvedMember: 10 })
    expect(await screen.findByRole("button", { name: /apply 0 rows/i })).toBeDisabled()
  })
})
