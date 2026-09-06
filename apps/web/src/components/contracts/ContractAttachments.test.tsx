import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

import { ContractAttachments } from "./ContractAttachments"

const mocks = vi.hoisted(() => ({
  list: vi.fn(),
  upload: vi.fn(),
  download: vi.fn(),
  canWrite: true,
}))
vi.mock("@/api/endpoints/documents", () => ({
  documentsApi: {
    list: mocks.list,
    uploadContractAttachment: mocks.upload,
    download: mocks.download,
  },
}))
vi.mock("@/hooks/useCanWrite", () => ({ useCanWrite: () => mocks.canWrite }))

beforeEach(() => {
  vi.clearAllMocks()
  mocks.canWrite = true
  mocks.list.mockResolvedValue({ items: [], total: 0 })
})

describe("contract attachments", () => {
  it("uploads to the selected contract and reloads persisted attachments", async () => {
    const user = userEvent.setup()
    const view = renderWithProviders(<ContractAttachments contractId="contract-1" />)
    await screen.findByText("No attachments yet.")
    const document = {
      id: "document-1",
      name: "Signed agreement.pdf",
      file_path: "private/file",
      created_at: "2026-09-05",
      file_size: 1024,
    }
    mocks.upload.mockResolvedValue(document)
    mocks.list.mockResolvedValue({ items: [document], total: 1 })
    const file = new File(["%PDF-1.7"], "Signed agreement.pdf", { type: "application/pdf" })
    await user.upload(screen.getByLabelText("Attach a file"), file)
    await waitFor(() => expect(mocks.upload).toHaveBeenCalledExactlyOnceWith("contract-1", file))
    expect(await screen.findByText("Signed agreement.pdf")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Download Signed agreement.pdf" })).toBeEnabled()
    view.unmount()
    renderWithProviders(<ContractAttachments contractId="contract-1" />)
    expect(await screen.findByText("Signed agreement.pdf")).toBeInTheDocument()
    expect(mocks.list).toHaveBeenLastCalledWith({ contract_id: "contract-1", page: 1, limit: 20 })
  })

  it("shows upload failures without a successful attachment", async () => {
    const user = userEvent.setup()
    mocks.upload.mockRejectedValue(new Error("Upload unavailable"))
    renderWithProviders(<ContractAttachments contractId="contract-1" />)
    await user.upload(
      screen.getByLabelText("Attach a file"),
      new File(["%PDF-1.7"], "agreement.pdf", { type: "application/pdf" }),
    )
    expect(await screen.findByRole("alert")).toHaveTextContent("Upload unavailable")
    expect(screen.queryByRole("button", { name: /Download/ })).not.toBeInTheDocument()
    expect(screen.getByLabelText("Attach a file")).toBeEnabled()
  })

  it("keeps attachments readable without upload controls for viewers", async () => {
    mocks.canWrite = false
    renderWithProviders(<ContractAttachments contractId="contract-1" />)
    await screen.findByText("No attachments yet.")
    expect(screen.queryByLabelText("Attach a file")).not.toBeInTheDocument()
    expect(mocks.list).toHaveBeenCalledOnce()
  })
})
