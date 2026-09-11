import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import type { MemberImportBatch, MemberImportRow } from "@/api/endpoints/members"
import { renderWithProviders } from "@/test/utils"
import { ApiError } from "@/types/api"

const api = vi.hoisted(() => ({
  stageImport: vi.fn(),
  listImportRows: vi.fn(),
  setImportRowDecision: vi.fn(),
  applyImport: vi.fn(),
  getImportTemplate: vi.fn(),
  abandonImport: vi.fn(),
}))
vi.mock("@/api/endpoints/members", () => ({ membersApi: api }))

const { MemberImportDialog } = await import("@/components/members/MemberImportDialog")

const EMPLOYMENT_HEADERS = [
  "Job title",
  "Classification",
  "Skill",
  "Department",
  "Unit",
  "Contract",
]

const BATCH: MemberImportBatch = {
  id: "batch-1",
  tenant_id: "tenant-1",
  file_name: "roster.csv",
  file_hash: "hash",
  row_count: 1,
  status: "Staged",
  outcome_counts: { New: 1 },
  staged_by: "user-1",
  applied_by: null,
  applied_at: null,
  created_at: "2026-09-10T00:00:00Z",
}

function makeRow(overrides: Partial<MemberImportRow> = {}): MemberImportRow {
  return {
    id: "row-1",
    row_number: 2,
    client_code: "IM",
    client_name: "Imaginary Bank",
    import_source_id: "IM-1",
    staff_number: "1001",
    display_label: "Amina Namukasa",
    outcome: "New",
    decision: "import",
    ...overrides,
  }
}

async function stage(rows: MemberImportRow[]) {
  api.stageImport.mockResolvedValue({ ...BATCH, row_count: rows.length })
  api.listImportRows.mockResolvedValue({
    items: rows,
    total: rows.length,
    page: 1,
    limit: 200,
    has_more: false,
  })
  renderWithProviders(<MemberImportDialog open onOpenChange={() => {}} onImported={() => {}} />)
  const input = screen.getByLabelText(/csv/i)
  await userEvent.upload(input, new File(["header\n"], "roster.csv", { type: "text/csv" }))
  await waitFor(() => expect(api.listImportRows).toHaveBeenCalled())
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe("member import preview", () => {
  it("omits the employment columns when the roster carried none", async () => {
    await stage([makeRow()])
    expect(await screen.findByText("Amina Namukasa")).toBeInTheDocument()
    for (const header of EMPLOYMENT_HEADERS) {
      expect(screen.queryByRole("columnheader", { name: header })).not.toBeInTheDocument()
    }
  })

  it("shows every employment column once a roster carries them", async () => {
    await stage([
      makeRow({
        employment: {
          job_title: "Branch Manager",
          job_classification: "Manager",
          skill: "Officer",
          department: "Operations",
          unit: "Kampala Road branch",
          employment_type: "Permanent",
        },
      }),
    ])
    expect(await screen.findByText("Amina Namukasa")).toBeInTheDocument()
    for (const header of EMPLOYMENT_HEADERS) {
      expect(screen.getByRole("columnheader", { name: header })).toBeInTheDocument()
    }
    expect(screen.getByText("Branch Manager")).toBeInTheDocument()
    expect(screen.getByText("Operations")).toBeInTheDocument()
    expect(screen.getByText("Kampala Road branch")).toBeInTheDocument()
    expect(screen.getByText("Permanent")).toBeInTheDocument()
  })

  it("keeps the columns aligned when only some rows carry employment", async () => {
    await stage([
      makeRow({ id: "row-1", employment: { department: "Treasury" } }),
      makeRow({ id: "row-2", row_number: 3, display_label: "Joan Aciro" }),
    ])
    expect(await screen.findByText("Joan Aciro")).toBeInTheDocument()
    const [, described, bare] = screen.getAllByRole("row")
    expect(described.querySelectorAll("td")).toHaveLength(13)
    expect(bare.querySelectorAll("td")).toHaveLength(13)
    expect(screen.getByText("Treasury")).toBeInTheDocument()
  })

  it("tells the uploader these columns are imported before they stage a file", () => {
    renderWithProviders(<MemberImportDialog open onOpenChange={() => {}} onImported={() => {}} />)
    expect(
      screen.getByText(/Job Title, Job Classification, Skill, Department, Unit and Contract type/),
    ).toBeInTheDocument()
    expect(screen.queryByText(/Other workforce columns are ignored/)).not.toBeInTheDocument()
  })

  it("hides the field help once a batch is staged, to give the table the room back", async () => {
    await stage([makeRow()])
    expect(
      screen.queryByText(
        /Job Title, Job Classification, Skill, Department, Unit and Contract type/,
      ),
    ).not.toBeInTheDocument()
  })
})

describe("chunked apply", () => {
  it("polls the apply endpoint until done, refreshing the table once at the end", async () => {
    await stage([makeRow()])
    api.applyImport
      .mockResolvedValueOnce({
        batch_id: "batch-1",
        imported: 0,
        updated: 0,
        unchanged: 0,
        failed: 0,
        remaining: 1,
        done: false,
      })
      .mockResolvedValueOnce({
        batch_id: "batch-1",
        imported: 1,
        updated: 0,
        unchanged: 0,
        failed: 0,
        remaining: 0,
        done: true,
      })

    await userEvent.click(screen.getByRole("button", { name: "Import 1 rows" }))

    await waitFor(() => expect(api.applyImport).toHaveBeenCalledTimes(2))
    expect(api.applyImport).toHaveBeenNthCalledWith(1, "batch-1", 200)
    expect(api.applyImport).toHaveBeenNthCalledWith(2, "batch-1", 200)
    // Initial stage, then one refresh once every chunk is written. Refreshing
    // between chunks paged through the whole batch again for each one.
    expect(api.listImportRows).toHaveBeenCalledTimes(2)
    await screen.findByRole("button", { name: "Done" })
    expect(screen.queryByRole("button", { name: "Cancel" })).not.toBeInTheDocument()
  })

  it("shows live count and percentage while a chunk is in flight, and stops on cancel", async () => {
    await stage([makeRow({ id: "row-1" }), makeRow({ id: "row-2", row_number: 3 })])
    const resolvers: Array<(value: unknown) => void> = []
    api.applyImport.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolvers.push(resolve)
        }),
    )

    await userEvent.click(screen.getByRole("button", { name: "Import 2 rows" }))
    const cancelButton = await screen.findByRole("button", { name: "Cancel" })

    resolvers[0]({
      batch_id: "batch-1",
      imported: 1,
      updated: 0,
      unchanged: 0,
      failed: 0,
      remaining: 1,
      done: false,
    })
    await screen.findByText("1 / 2 · 50%")
    await waitFor(() => expect(resolvers).toHaveLength(2))

    // Cancel takes effect after the in-flight chunk finishes, not mid-request.
    await userEvent.click(cancelButton)
    resolvers[1]({
      batch_id: "batch-1",
      imported: 1,
      updated: 0,
      unchanged: 0,
      failed: 0,
      remaining: 0,
      done: false,
    })

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Cancel" })).not.toBeInTheDocument(),
    )
    expect(api.applyImport).toHaveBeenCalledTimes(2)
  })

  it("counts a row written before a cancel as written, not skipped, in the summary", async () => {
    const rowOne = makeRow({ id: "row-1" })
    const rowTwo = makeRow({ id: "row-2", row_number: 3 })
    await stage([rowOne, rowTwo])

    api.listImportRows.mockResolvedValueOnce({
      items: [{ ...rowOne, imported_member_id: "member-1" }, rowTwo],
      total: 2,
      page: 1,
      limit: 200,
      has_more: false,
    })
    let resolveChunk: (value: unknown) => void = () => {}
    api.applyImport.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveChunk = resolve
        }),
    )

    await userEvent.click(screen.getByRole("button", { name: "Import 2 rows" }))
    const cancelButton = await screen.findByRole("button", { name: "Cancel" })
    await userEvent.click(cancelButton)
    resolveChunk({
      batch_id: "batch-1",
      imported: 1,
      updated: 0,
      unchanged: 0,
      failed: 0,
      remaining: 1,
      done: false,
    })
    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Cancel" })).not.toBeInTheDocument(),
    )

    await waitFor(() => {
      const summary = screen.getByText(
        (_, node) => node?.tagName === "P" && Boolean(node.textContent?.includes("rows checked")),
      )
      expect(summary.textContent).toBe(
        "2 rows checked · 1 ready · 1 already written · 0 skipped · 0 errors",
      )
    })
  })

  it("treats a lost connection as recoverable, not data loss, and refreshes what already wrote", async () => {
    const rowOne = makeRow({ id: "row-1" })
    const rowTwo = makeRow({ id: "row-2", row_number: 3 })
    await stage([rowOne, rowTwo])

    api.listImportRows.mockResolvedValueOnce({
      items: [{ ...rowOne, imported_member_id: "member-1" }, rowTwo],
      total: 2,
      page: 1,
      limit: 200,
      has_more: false,
    })
    api.applyImport.mockRejectedValueOnce(
      new ApiError("Request timeout: The request took too long", "TIMEOUT_ERROR", 0),
    )

    await userEvent.click(screen.getByRole("button", { name: "Import 2 rows" }))

    expect(
      await screen.findByText(
        "Lost the connection partway through, but nothing already written was lost. Click Import to resume.",
      ),
    ).toBeInTheDocument()
    // The row a prior, already-committed chunk wrote still shows as Imported.
    expect(await screen.findByText("Imported")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Import 1 rows" })).toBeInTheDocument()
  })
})

describe("updating a member the roster already created", () => {
  const matched = (overrides: Partial<MemberImportRow> = {}) =>
    makeRow({
      outcome: "Duplicate",
      decision: "skip",
      matched_member_id: "member-1",
      ...overrides,
    })

  it("offers Update and Skip on a duplicate that matched a member", async () => {
    await stage([matched()])

    await userEvent.click(screen.getByRole("combobox", { name: "Decision for row 2" }))

    expect(await screen.findByRole("option", { name: "Update" })).toBeInTheDocument()
    expect(screen.getByRole("option", { name: "Skip" })).toBeInTheDocument()
    expect(screen.queryByRole("option", { name: "Import" })).not.toBeInTheDocument()
  })

  it("leaves a duplicate that matched nobody with no decision to make", async () => {
    await stage([
      matched({ matched_member_id: null, message: "Already staged as row 7 of batch b-9" }),
    ])

    expect(screen.queryByRole("combobox", { name: "Decision for row 2" })).not.toBeInTheDocument()
    expect(screen.getByText("Already staged as row 7 of batch b-9")).toBeInTheDocument()
  })

  it("never queues a matched duplicate until someone chooses Update", async () => {
    await stage([matched()])
    expect(screen.getByRole("button", { name: "Import 0 rows" })).toBeDisabled()
  })

  it("counts a row set to Update towards the apply button, naming it as an update", async () => {
    api.setImportRowDecision.mockResolvedValue(matched({ decision: "update" }))
    await stage([matched()])

    await userEvent.click(screen.getByRole("combobox", { name: "Decision for row 2" }))
    await userEvent.click(await screen.findByRole("option", { name: "Update" }))

    await waitFor(() =>
      expect(api.setImportRowDecision).toHaveBeenCalledWith("batch-1", "row-1", "update"),
    )
    expect(await screen.findByRole("button", { name: "Update 1 members" })).toBeEnabled()
    expect(screen.getByText("Will update")).toBeInTheDocument()
  })

  it("reports updates apart from imports once the batch is applied", async () => {
    api.setImportRowDecision.mockResolvedValue(matched({ decision: "update" }))
    await stage([matched()])
    await userEvent.click(screen.getByRole("combobox", { name: "Decision for row 2" }))
    await userEvent.click(await screen.findByRole("option", { name: "Update" }))
    await waitFor(() => expect(api.setImportRowDecision).toHaveBeenCalled())

    api.listImportRows.mockResolvedValue({
      items: [matched({ decision: "update", imported_member_id: "member-1" })],
      total: 1,
      page: 1,
      limit: 200,
      has_more: false,
    })
    api.applyImport.mockResolvedValue({
      batch_id: "batch-1",
      imported: 0,
      updated: 1,
      unchanged: 0,
      failed: 0,
      remaining: 0,
      done: true,
    })

    await userEvent.click(screen.getByRole("button", { name: "Update 1 members" }))

    expect(await screen.findByText("Updated")).toBeInTheDocument()
    expect(screen.getByText(/updated/)).toBeInTheDocument()
  })
})

describe("restage conflict", () => {
  it("offers to discard the stuck batch and retries staging after confirming", async () => {
    api.stageImport
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
      .mockResolvedValueOnce({ ...BATCH, row_count: 1 })
    api.listImportRows.mockResolvedValue({
      items: [makeRow()],
      total: 1,
      page: 1,
      limit: 200,
      has_more: false,
    })
    api.abandonImport.mockResolvedValue({ ...BATCH, id: "b-1", status: "Abandoned" })

    renderWithProviders(<MemberImportDialog open onOpenChange={() => {}} onImported={() => {}} />)
    const input = screen.getByLabelText(/csv/i)
    await userEvent.upload(input, new File(["header\n"], "roster.csv", { type: "text/csv" }))

    const discardLink = await screen.findByText("Discard the stuck batch and retry")
    await userEvent.click(discardLink)
    await userEvent.click(await screen.findByRole("button", { name: "Discard and retry" }))

    await waitFor(() =>
      expect(api.abandonImport).toHaveBeenCalledWith(
        "b-1",
        "Discarded from the import dialog after a restage conflict",
      ),
    )
    expect(api.stageImport).toHaveBeenCalledTimes(2)
    expect(await screen.findByText("Amina Namukasa")).toBeInTheDocument()
  })
})
