/**
 * The staged import: nothing is written until a person applies it, and the
 * outcome counts are what tells them whether applying is worth doing.
 */

import { waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { SessionImportDialog } from "@/components/sessions/SessionImportDialog"
import { renderWithProviders } from "@/test/utils"
import { ApiError } from "@/types/api"

const stage = vi.fn()
const apply = vi.fn()
const listRows = vi.fn()
const getBatch = vi.fn()
const getTemplate = vi.fn()
const abandon = vi.fn()

vi.mock("@/api/endpoints/session-imports", () => ({
  sessionImportsApi: {
    stage: (...args: unknown[]) => stage(...args),
    apply: (...args: unknown[]) => apply(...args),
    listRows: (...args: unknown[]) => listRows(...args),
    getBatch: (...args: unknown[]) => getBatch(...args),
    getTemplate: (...args: unknown[]) => getTemplate(...args),
    abandon: (...args: unknown[]) => abandon(...args),
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

describe("template", () => {
  it("downloads the server-generated template on request", async () => {
    getTemplate.mockResolvedValue(new Blob(["Date,Company (CLEAN)\n"], { type: "text/csv" }))
    const screen = renderWithProviders(
      <SessionImportDialog open onOpenChange={() => {}} onImported={() => {}} />,
    )
    await userEvent.click(screen.getByRole("button", { name: /template/i }))
    expect(getTemplate).toHaveBeenCalledOnce()
  })
})

describe("chunked apply", () => {
  it("polls the apply endpoint until done, refreshing the batch after each chunk", async () => {
    const screen = await stageFile({ Accepted: 2 })
    getBatch.mockResolvedValue(batch({ Accepted: 2 }))
    apply
      .mockResolvedValueOnce({ batch_id: "b_1", imported: 1, failed: 0, remaining: 1, done: false })
      .mockResolvedValueOnce({ batch_id: "b_1", imported: 1, failed: 0, remaining: 0, done: true })

    await userEvent.click(screen.getByRole("button", { name: /apply 2 rows/i }))

    await waitFor(() => expect(apply).toHaveBeenCalledTimes(2))
    expect(apply).toHaveBeenNthCalledWith(1, "b_1", 50)
    expect(apply).toHaveBeenNthCalledWith(2, "b_1", 50)
    expect(await screen.findByText(/imported 2 sessions/i)).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Cancel" })).not.toBeInTheDocument()
  })

  it("shows live count and percentage while a chunk is in flight, and stops on cancel", async () => {
    const screen = await stageFile({ Accepted: 2 })
    getBatch.mockResolvedValue(batch({ Accepted: 2 }))
    const resolvers: Array<(value: unknown) => void> = []
    apply.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolvers.push(resolve)
        }),
    )

    await userEvent.click(screen.getByRole("button", { name: /apply 2 rows/i }))
    const cancelButton = await screen.findByRole("button", { name: "Cancel" })

    resolvers[0]({ batch_id: "b_1", imported: 1, failed: 0, remaining: 1, done: false })
    await screen.findByText("1 / 2 · 50%")
    await waitFor(() => expect(resolvers).toHaveLength(2))

    await userEvent.click(cancelButton)
    resolvers[1]({ batch_id: "b_1", imported: 1, failed: 0, remaining: 0, done: false })

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Cancel" })).not.toBeInTheDocument(),
    )
    expect(apply).toHaveBeenCalledTimes(2)
  })

  it("treats a lost connection as recoverable, not data loss", async () => {
    const screen = await stageFile({ Accepted: 2 })
    getBatch.mockResolvedValue(batch({ Accepted: 2 }))
    apply.mockRejectedValueOnce(
      new ApiError("Request timeout: The request took too long", "TIMEOUT_ERROR", 0),
    )

    await userEvent.click(screen.getByRole("button", { name: /apply 2 rows/i }))

    expect(
      await screen.findByText(
        "Lost the connection partway through, but nothing already written was lost. Click Apply to resume.",
      ),
    ).toBeInTheDocument()
  })
})

describe("source system", () => {
  it("always stages against the activity-log workbook, with no source-key column", async () => {
    await stageFile({ Accepted: 1 })
    expect(stage).toHaveBeenCalledWith(expect.any(File), "activity-log-workbook")
  })
})

describe("restage conflict", () => {
  it("offers to discard the stuck batch and retries staging after confirming", async () => {
    stage
      .mockRejectedValueOnce(
        new ApiError(
          "This file was already staged as batch b-1",
          "IMPORT_ALREADY_STAGED",
          409,
          undefined,
          undefined,
          [{ field: "batch_id", message: "b-1", code: null }],
        ),
      )
      .mockResolvedValueOnce(batch({ Accepted: 1 }))
    listRows.mockResolvedValue({ items: [], total: 0, page: 1, limit: 50 })
    abandon.mockResolvedValue({ id: "b-1", status: "Abandoned" })

    const screen = renderWithProviders(
      <SessionImportDialog open onOpenChange={() => {}} onImported={() => {}} />,
    )
    const file = new File(["DATE\n2025-09-12\n"], "sessions.csv", { type: "text/csv" })
    await userEvent.upload(screen.getByLabelText("CSV file"), file)
    await userEvent.click(screen.getByRole("button", { name: /stage file/i }))

    const discardLink = await screen.findByText("Discard the stuck batch and retry")
    await userEvent.click(discardLink)
    await userEvent.click(await screen.findByRole("button", { name: "Discard and retry" }))

    await waitFor(() =>
      expect(abandon).toHaveBeenCalledWith(
        "b-1",
        "Discarded from the import dialog after a restage conflict",
      ),
    )
    expect(stage).toHaveBeenCalledTimes(2)
    expect(await screen.findByRole("button", { name: /apply 1 rows/i })).toBeEnabled()
  })
})
