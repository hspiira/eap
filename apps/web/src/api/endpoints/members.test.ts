import { beforeEach, describe, expect, it, vi } from "vitest"

import { membersApi } from "@/api/endpoints/members"
import { EligibilityStatus, MemberRelation } from "@/types/enums"

const api = vi.hoisted(() => ({
  get: vi.fn(),
  getBlob: vi.fn(),
  patch: vi.fn(),
  post: vi.fn(),
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
})
