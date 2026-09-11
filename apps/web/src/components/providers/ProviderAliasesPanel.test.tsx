import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { ProviderAliasesPanel } from "@/components/providers/ProviderAliasesPanel"
import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({
  list: vi.fn(),
  adopt: vi.fn(),
  role: "Admin" as string,
  showSuccess: vi.fn(),
  showError: vi.fn(),
}))

vi.mock("@/api/endpoints/provider-aliases", () => ({
  providerAliasesApi: { list: mocks.list, adopt: mocks.adopt },
}))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => true,
  useCurrentRole: () => mocks.role,
}))
vi.mock("@/store/slices/tenantSlice", () => ({
  useTenantStore: (select: (s: { currentTenantId: string }) => unknown) =>
    select({ currentTenantId: "tenant-1" }),
}))
// Partial: the test wrapper still renders the real ToastProvider.
vi.mock("@/contexts/ToastContext", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  useToast: () => ({ showSuccess: mocks.showSuccess, showError: mocks.showError }),
}))

function page(items: unknown[]) {
  return { items, total: items.length, page: 1, limit: 50, has_more: false }
}

function panel() {
  return renderWithProviders(<ProviderAliasesPanel providerId="prv-1" displayName="Amina Okello" />)
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.role = "Admin"
  mocks.list.mockResolvedValue(page([]))
  mocks.adopt.mockResolvedValue({ alias: { id: "alias-1" }, claimed: true })
})

describe("names in imports", () => {
  it("asks only for the spellings resolved to this practitioner", async () => {
    panel()
    await waitFor(() => expect(mocks.list).toHaveBeenCalled())
    expect(mocks.list).toHaveBeenCalledWith(
      expect.objectContaining({
        tenant_id: "tenant-1",
        provider_id: "prv-1",
        source_system: "activity-log-workbook",
      }),
    )
  })

  it("lists the spellings the activity log uses", async () => {
    mocks.list.mockResolvedValue(page([{ id: "a1", source_value: "DR. A. OKELLO" }]))
    panel()
    expect(await screen.findByText("DR. A. OKELLO")).toBeInTheDocument()
  })

  it("says what an empty list costs rather than just showing nothing", async () => {
    panel()
    expect(await screen.findByText(/will stall until one is/i)).toBeInTheDocument()
  })

  it("records a new spelling against this practitioner", async () => {
    const user = userEvent.setup()
    panel()
    await user.type(await screen.findByLabelText(/add a spelling/i), "DR. A. OKELLO")
    await user.click(screen.getByRole("button", { name: "Add" }))

    await waitFor(() =>
      expect(mocks.adopt).toHaveBeenCalledWith(
        "tenant-1",
        "activity-log-workbook",
        "DR. A. OKELLO",
        "prv-1",
      ),
    )
  })

  it("refuses to move a spelling that already names somebody else", async () => {
    mocks.adopt.mockResolvedValue({ alias: { id: "a1" }, claimed: false })
    const user = userEvent.setup()
    panel()
    await user.type(await screen.findByLabelText(/add a spelling/i), "DR. A. OKELLO")
    await user.click(screen.getByRole("button", { name: "Add" }))

    await waitFor(() => expect(mocks.showError).toHaveBeenCalled())
    expect(mocks.showError.mock.calls[0][0]).toMatch(/already names another practitioner/i)
  })

  it("shows a non-admin the spellings but no way to add one", async () => {
    mocks.role = "User"
    mocks.list.mockResolvedValue(page([{ id: "a1", source_value: "DR. A. OKELLO" }]))
    panel()
    expect(await screen.findByText("DR. A. OKELLO")).toBeInTheDocument()
    expect(screen.queryByLabelText(/add a spelling/i)).not.toBeInTheDocument()
  })
})
