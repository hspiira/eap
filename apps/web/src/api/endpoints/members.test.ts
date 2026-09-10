import { beforeEach, describe, expect, it, vi } from "vitest"

import { membersApi } from "@/api/endpoints/members"
import { EligibilityStatus, MemberRelation } from "@/types/enums"

const api = vi.hoisted(() => ({
  get: vi.fn(),
  getBlob: vi.fn(),
  patch: vi.fn(),
  post: vi.fn(),
  postFormData: vi.fn(),
}))

vi.mock("@/api/client", () => ({ default: api }))

describe("membersApi", () => {
  beforeEach(() => vi.clearAllMocks())

  it("lists members with server-side roster filters", async () => {
    api.get.mockResolvedValue({ items: [], total: 0, page: 1, limit: 20, has_more: false })
    const params = {
      client_id: "client-1",
      relation: MemberRelation.EMPLOYEE,
      status: EligibilityStatus.ACTIVE,
      search: "HR-12",
    }

    await membersApi.list(params)

    expect(api.get).toHaveBeenCalledWith("/members", params)
  })

  it("exports either the selected IDs or the current filters", async () => {
    api.getBlob.mockResolvedValue(new Blob(["id\nmember-1\n"], { type: "text/csv" }))

    await membersApi.exportCsv({ member_ids: ["member-1", "member-2"] })

    expect(api.getBlob).toHaveBeenCalledWith("/members/export", {
      member_ids: ["member-1", "member-2"],
    })
  })

  it("maps lifecycle actions to their dedicated member endpoints", async () => {
    api.post.mockResolvedValue({ id: "member-1" })

    await membersApi.suspend("member-1")
    await membersApi.reinstate("member-1")
    await membersApi.terminate("member-1")

    expect(api.post).toHaveBeenNthCalledWith(1, "/members/member-1/suspend")
    expect(api.post).toHaveBeenNthCalledWith(2, "/members/member-1/reinstate")
    expect(api.post).toHaveBeenNthCalledWith(3, "/members/member-1/terminate")
  })

  it("loads the employee's beneficiaries through the relationship endpoint", async () => {
    api.get.mockResolvedValue([])

    await membersApi.listBeneficiaries("member-1")

    expect(api.get).toHaveBeenCalledWith("/members/member-1/beneficiaries")
  })

  it("stages a roster upload as multipart form data", async () => {
    api.postFormData.mockResolvedValue({ id: "batch-1" })
    const file = new File(["Company Code,Staff_ID\n"], "members.csv", { type: "text/csv" })

    await membersApi.stageImport(file)

    expect(api.postFormData).toHaveBeenCalledWith("/members/import", expect.any(FormData))
  })

  it("lists staged rows with pagination", async () => {
    api.get.mockResolvedValue({ items: [], total: 0, page: 1, limit: 200, has_more: false })

    await membersApi.listImportRows("batch-1", { page: 2, limit: 200 })

    expect(api.get).toHaveBeenCalledWith("/members/import/batch-1/rows", { page: 2, limit: 200 })
  })

  it("patches one row's Import/Skip decision", async () => {
    api.patch.mockResolvedValue({ id: "row-1", decision: "skip" })

    await membersApi.setImportRowDecision("batch-1", "row-1", "skip")

    expect(api.patch).toHaveBeenCalledWith("/members/import/batch-1/rows/row-1", {
      decision: "skip",
    })
  })

  it("applies a staged batch with no request body, and a generous timeout", async () => {
    api.post.mockResolvedValue({ batch_id: "batch-1", imported: 1 })

    await membersApi.applyImport("batch-1")

    expect(api.post).toHaveBeenCalledWith(
      "/members/import/batch-1/apply",
      undefined,
      expect.objectContaining({ timeout: expect.any(Number) }),
    )
    const [, , options] = api.post.mock.calls[0]
    expect(options.timeout).toBeGreaterThan(30000)
  })

  it("puts the limit in the query string when applying a chunk", async () => {
    api.post.mockResolvedValue({ batch_id: "batch-1", imported: 1 })

    await membersApi.applyImport("batch-1", 50)

    expect(api.post).toHaveBeenCalledWith(
      "/members/import/batch-1/apply?limit=50",
      undefined,
      expect.objectContaining({ timeout: expect.any(Number) }),
    )
  })

  it("abandons a staged batch with a reason", async () => {
    api.post.mockResolvedValue({ id: "batch-1", status: "Abandoned" })

    await membersApi.abandonImport("batch-1", "wrong file")

    expect(api.post).toHaveBeenCalledWith("/members/import/batch-1/abandon", {
      reason: "wrong file",
    })
  })
})
