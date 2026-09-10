import { screen } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { makeMember } from "@/test/members"
import { renderWithProviders } from "@/test/utils"

const api = vi.hoisted(() => ({
  getById: vi.fn(),
  listBeneficiaries: vi.fn(),
  listNextOfKin: vi.fn(),
  listSessions: vi.fn(),
}))
vi.mock("@/api/endpoints/members", () => ({ membersApi: api }))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => false,
  useCurrentRole: () => "Viewer",
  useHasClinicalScope: () => ({ hasScope: false, isLoading: false }),
}))
vi.mock("@/components/MemberFormSheet", () => ({ MemberFormSheet: () => null }))
vi.mock("@/components/MemberNextOfKinFormSheet", () => ({ MemberNextOfKinFormSheet: () => null }))
vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (options: unknown) => ({
    options,
    useParams: () => ({ memberId: "member-1" }),
  }),
  Link: ({ children }: { children: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
}))

const { Route } = await import("@/routes/members/$memberId")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

beforeEach(() => {
  vi.clearAllMocks()
  api.getById.mockResolvedValue(makeMember())
  api.listBeneficiaries.mockResolvedValue([])
  api.listNextOfKin.mockResolvedValue([])
})

describe("member detail", () => {
  it("transitions from loading into details without changing hook order", async () => {
    renderWithProviders(<Page />)
    expect(screen.getByRole("status", { name: "Loading" })).toBeInTheDocument()
    expect(await screen.findByRole("heading", { name: "Amina Namukasa" })).toBeInTheDocument()
    expect(await screen.findByText("No beneficiaries linked.")).toBeInTheDocument()
    expect(await screen.findByText("No next-of-kin contacts recorded.")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Suspend" })).not.toBeInTheDocument()
    expect(screen.getByRole("tab", { name: "Service history" })).toBeDisabled()
    expect(screen.getByRole("tab", { name: "Account access" })).toBeEnabled()
    expect(screen.queryByText("client-1")).not.toBeInTheDocument()
  })

  it("shows contact and beneficiary failures separately from empty results", async () => {
    api.listBeneficiaries.mockRejectedValue(new Error("Unavailable"))
    api.listNextOfKin.mockRejectedValue(new Error("Unavailable"))
    renderWithProviders(<Page />)
    expect(await screen.findByText("Could not load contacts.")).toBeInTheDocument()
    expect(await screen.findByText("Could not load beneficiaries.")).toBeInTheDocument()
    expect(screen.queryByText("No beneficiaries linked.")).not.toBeInTheDocument()
    expect(screen.queryByText("No next-of-kin contacts recorded.")).not.toBeInTheDocument()
  })

  it("does not start relationship requests when the member cannot be loaded", async () => {
    api.getById.mockRejectedValue(new Error("Not found"))
    renderWithProviders(<Page />)
    expect(await screen.findByText("Member not found")).toBeInTheDocument()
    expect(api.listBeneficiaries).not.toHaveBeenCalled()
    expect(api.listNextOfKin).not.toHaveBeenCalled()
  })

  it("shows the employment card only when the employer supplied those details", async () => {
    renderWithProviders(<Page />)
    expect(await screen.findByRole("heading", { name: "Amina Namukasa" })).toBeInTheDocument()
    expect(screen.queryByText("Employment")).not.toBeInTheDocument()
  })

  it("renders the employment details an employer did supply", async () => {
    api.getById.mockResolvedValue(
      makeMember({
        employment: {
          job_title: "Branch Manager",
          job_classification: "Manager",
          skill: "Officer",
          department: "Operations",
          unit: "Kampala Road branch",
          employment_type: "Permanent",
        },
      }),
    )
    renderWithProviders(<Page />)
    expect(await screen.findByText("Employment")).toBeInTheDocument()
    expect(screen.getByText("Branch Manager")).toBeInTheDocument()
    expect(screen.getByText("Operations")).toBeInTheDocument()
    expect(screen.getByText("Kampala Road branch")).toBeInTheDocument()
    expect(screen.getByText("Permanent")).toBeInTheDocument()
  })
})
