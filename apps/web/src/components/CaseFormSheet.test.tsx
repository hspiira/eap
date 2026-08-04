import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

const listForClientMock = vi.fn()

vi.mock("@/api/endpoints/eligible-members", () => ({
  eligibleMembersApi: {
    listForClient: (...args: unknown[]) => listForClientMock(...args),
  },
}))

import { EligibleMemberPicker } from "@/components/CaseFormSheet"

beforeEach(() => {
  listForClientMock.mockReset().mockResolvedValue([
    { id: "mem-1", client_id: "c-1", employer_member_id: "EMP-0042", display_label: "" },
    { id: "mem-2", client_id: "c-1", employer_member_id: "EMP-0043", display_label: "Jane Doe" },
  ])
})

describe("EligibleMemberPicker", () => {
  it("falls back to the employer member id when display_label is blank, without a stray bullet", async () => {
    renderWithProviders(<EligibleMemberPicker clientId="c-1" value="" onChange={vi.fn()} />)
    expect(await screen.findByText("EMP-0042")).toBeInTheDocument()
    expect(screen.queryByText("· EMP-0042")).not.toBeInTheDocument()
  })

  it("shows display_label alongside the employer member id when present", async () => {
    renderWithProviders(<EligibleMemberPicker clientId="c-1" value="" onChange={vi.fn()} />)
    expect(await screen.findByText("Jane Doe · EMP-0043")).toBeInTheDocument()
  })

  it("filters the roster by typing, client-side", async () => {
    const user = userEvent.setup()
    renderWithProviders(<EligibleMemberPicker clientId="c-1" value="" onChange={vi.fn()} />)
    await screen.findByText("EMP-0042")
    await user.type(screen.getByPlaceholderText(/search by name or member number/i), "Jane")
    expect(screen.queryByText("EMP-0042")).not.toBeInTheDocument()
    expect(screen.getByText("Jane Doe · EMP-0043")).toBeInTheDocument()
  })

  it("selecting a member calls onChange with its id", async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    renderWithProviders(<EligibleMemberPicker clientId="c-1" value="" onChange={onChange} />)
    await user.click(await screen.findByText("Jane Doe · EMP-0043"))
    expect(onChange).toHaveBeenCalledWith("mem-2")
  })
})
