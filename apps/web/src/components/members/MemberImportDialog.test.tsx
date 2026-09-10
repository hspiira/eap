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
  it("polls the apply endpoint until done, refreshing the table after each chunk", async () => {
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
    expect(api.listImportRows).toHaveBeenCalledTimes(3) // initial stage + one refresh per chunk
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
