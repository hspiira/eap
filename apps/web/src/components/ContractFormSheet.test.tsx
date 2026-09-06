import { screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

import { ContractFormSheet } from "./ContractFormSheet"

const mocks = vi.hoisted(() => ({
  create: vi.fn(),
  upload: vi.fn(),
  getClient: vi.fn(),
}))
vi.mock("@/api/endpoints/contracts", () => ({ contractsApi: { create: mocks.create } }))
vi.mock("@/api/endpoints/documents", () => ({
  documentsApi: { uploadContractAttachment: mocks.upload },
}))
vi.mock("@/api/endpoints/clients", () => ({ clientsApi: { getById: mocks.getClient } }))

const file = (name: string) => new File(["x"], name, { type: "application/pdf" })

async function fillRequired(user: ReturnType<typeof userEvent.setup>) {
  const form = within(screen.getByRole("dialog"))
  await user.type(form.getByLabelText(/Start date/), "2026-01-01")
  await user.type(form.getByLabelText(/End date/), "2026-12-31")
  await user.type(form.getByLabelText(/Billing rate/), "5000000")
  return form
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.create.mockResolvedValue({ id: "contract-1" })
  mocks.upload.mockResolvedValue({ id: "doc-1" })
  mocks.getClient.mockResolvedValue({ id: "client-1", name: "Acme", code: "ACME" })
})

describe("ContractFormSheet attachments", () => {
  it("uploads queued files against the contract once it exists", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ContractFormSheet open onOpenChange={vi.fn()} clientId="client-1" />)
    const form = await fillRequired(user)
    await user.upload(form.getByLabelText(/Attachments/), [file("msa.pdf"), file("rates.pdf")])

    expect(form.getByText("msa.pdf")).toBeInTheDocument()
    await user.click(form.getByRole("button", { name: "Create contract" }))

    await waitFor(() => expect(mocks.create).toHaveBeenCalled())
    await waitFor(() => expect(mocks.upload).toHaveBeenCalledTimes(2))
    expect(mocks.upload.mock.calls[0][0]).toBe("contract-1")
    expect(mocks.upload.mock.calls[0][1].name).toBe("msa.pdf")
  })

  it("lets a queued file be removed before saving", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ContractFormSheet open onOpenChange={vi.fn()} clientId="client-1" />)
    const form = await fillRequired(user)
    await user.upload(form.getByLabelText(/Attachments/), file("draft.pdf"))
    await user.click(form.getByRole("button", { name: "Remove draft.pdf" }))

    expect(form.queryByText("draft.pdf")).toBeNull()
    await user.click(form.getByRole("button", { name: "Create contract" }))
    await waitFor(() => expect(mocks.create).toHaveBeenCalled())
    expect(mocks.upload).not.toHaveBeenCalled()
  })

  it("keeps the saved contract when an upload fails, and says which", async () => {
    mocks.upload.mockRejectedValueOnce(new Error("boom"))
    const user = userEvent.setup()
    renderWithProviders(<ContractFormSheet open onOpenChange={vi.fn()} clientId="client-1" />)
    const form = await fillRequired(user)
    await user.upload(form.getByLabelText(/Attachments/), file("msa.pdf"))
    await user.click(form.getByRole("button", { name: "Create contract" }))

    await waitFor(() => expect(mocks.create).toHaveBeenCalled())
    expect(await screen.findByText(/did not upload: msa\.pdf/)).toBeInTheDocument()
  })

  it("rejects a currency that is not three letters", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ContractFormSheet open onOpenChange={vi.fn()} clientId="client-1" />)
    const form = await fillRequired(user)
    const currency = form.getByLabelText(/Currency/)
    await user.clear(currency)
    await user.type(currency, "123")
    await user.click(form.getByRole("button", { name: "Create contract" }))

    expect(await screen.findByText(/ISO 3-letter currency code/)).toBeInTheDocument()
    expect(mocks.create).not.toHaveBeenCalled()
  })
})
