import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { MemberFormSheet } from "@/components/MemberFormSheet"
import { MemberNextOfKinFormSheet } from "@/components/MemberNextOfKinFormSheet"
import { Input } from "@/components/ui/input"
import { makeMember } from "@/test/members"
import { renderWithProviders } from "@/test/utils"

const api = vi.hoisted(() => ({
  create: vi.fn(),
  update: vi.fn(),
  createNextOfKin: vi.fn(),
  getClient: vi.fn(),
}))
vi.mock("@/api/endpoints/members", () => ({ membersApi: api }))
vi.mock("@/api/endpoints/clients", () => ({ clientsApi: { getById: api.getClient } }))
vi.mock("@/components/common/EntityPicker", () => ({
  ClientPicker: ({ value, onChange }: { value: string; onChange: (id: string) => void }) => (
    <Input aria-label="Client" value={value} onChange={(event) => onChange(event.target.value)} />
  ),
  EntityPicker: () => <div>Primary employee picker</div>,
  PickerRow: () => null,
}))

beforeEach(() => {
  vi.clearAllMocks()
  api.getClient.mockResolvedValue({ id: "client-1", name: "Acme" })
  api.create.mockResolvedValue(makeMember())
  api.update.mockResolvedValue(makeMember())
  api.createNextOfKin.mockResolvedValue({ id: "kin-1" })
})

describe("member forms", () => {
  it("creates a roster member with contextual client and blank optional fields as null", async () => {
    const user = userEvent.setup()
    renderWithProviders(<MemberFormSheet open onOpenChange={vi.fn()} clientId="client-1" />)
    await user.type(screen.getByRole("textbox", { name: "Name" }), " Amina ")
    await user.click(screen.getByRole("button", { name: "Add member" }))
    await waitFor(() =>
      expect(api.create).toHaveBeenCalledWith(
        expect.objectContaining({
          client_id: "client-1",
          display_label: "Amina",
          relation: "Employee",
          primary_employee_member_id: null,
          work_email: null,
          personal_email: null,
          phone: null,
          date_of_birth: null,
          gender: null,
        }),
      ),
    )
  })

  it("never offers a member code field, leaving the server to issue one", async () => {
    const user = userEvent.setup()
    renderWithProviders(<MemberFormSheet open onOpenChange={vi.fn()} clientId="client-1" />)
    expect(screen.queryByRole("textbox", { name: "Member code" })).toBeNull()

    await user.click(screen.getByRole("button", { name: "Add member" }))
    expect(await screen.findByText("Name is required")).toBeInTheDocument()
    expect(api.create).not.toHaveBeenCalled()

    await user.type(screen.getByRole("textbox", { name: "Name" }), "Amina")
    await user.click(screen.getByRole("button", { name: "Add member" }))
    await waitFor(() => expect(api.create).toHaveBeenCalled())
    expect(api.create.mock.calls[0][0]).not.toHaveProperty("employer_member_id")
  })

  it("sends the optional identification numbers when they are filled in", async () => {
    const user = userEvent.setup()
    renderWithProviders(<MemberFormSheet open onOpenChange={vi.fn()} clientId="client-1" />)
    await user.type(screen.getByRole("textbox", { name: "Name" }), "Amina")
    await user.type(screen.getByRole("textbox", { name: "Company ID number" }), "EMP-9")
    await user.type(screen.getByRole("textbox", { name: "National ID (NIN)" }), "CM12345")
    await user.type(screen.getByRole("textbox", { name: "Passport number" }), "B0987654")
    await user.click(screen.getByRole("button", { name: "Add member" }))
    await waitFor(() =>
      expect(api.create).toHaveBeenCalledWith(
        expect.objectContaining({
          staff_number: "EMP-9",
          national_id: "CM12345",
          passport_number: "B0987654",
        }),
      ),
    )
  })

  it("clears optional contact data on edit without changing client", async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemberFormSheet open onOpenChange={vi.fn()} member={makeMember({ phone: "123" })} />,
    )
    await user.clear(screen.getByLabelText("Phone", { exact: true }))
    await user.click(screen.getByRole("button", { name: "Save changes" }))
    await waitFor(() =>
      expect(api.update).toHaveBeenCalledWith("member-1", expect.objectContaining({ phone: null })),
    )
    expect(api.update.mock.calls[0][1]).not.toHaveProperty("client_id")
  })

  it("shows the issued member code on edit as read-only text, not an input", async () => {
    renderWithProviders(
      <MemberFormSheet
        open
        onOpenChange={vi.fn()}
        member={makeMember({ employer_member_id: "ACME-007" })}
      />,
    )
    expect(screen.getByText("ACME-007")).toBeInTheDocument()
    expect(screen.queryByRole("textbox", { name: "Member code" })).toBeNull()
  })

  it("leaves the member code out of an update payload", async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemberFormSheet open onOpenChange={vi.fn()} member={makeMember({ phone: "123" })} />,
    )
    await user.clear(screen.getByLabelText("Phone", { exact: true }))
    await user.click(screen.getByRole("button", { name: "Save changes" }))
    await waitFor(() => expect(api.update).toHaveBeenCalled())
    expect(api.update.mock.calls[0][1]).not.toHaveProperty("employer_member_id")
  })

  it("requires a next-of-kin contact method", async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemberNextOfKinFormSheet open onOpenChange={vi.fn()} memberId="member-1" />,
    )
    await user.type(screen.getByRole("textbox", { name: "Name" }), "Grace")
    await user.click(screen.getByRole("button", { name: "Add contact" }))
    expect(await screen.findByText("Phone or email is required")).toBeInTheDocument()
    expect(api.createNextOfKin).not.toHaveBeenCalled()
    await user.type(screen.getByLabelText("Phone", { exact: true }), "+256700000000")
    await user.click(screen.getByRole("button", { name: "Add contact" }))
    await waitFor(() =>
      expect(api.createNextOfKin).toHaveBeenCalledWith(
        "member-1",
        expect.objectContaining({ name: "Grace", phone: "+256700000000", email: null }),
      ),
    )
  })
})
