import { fireEvent, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { ProviderSpecialtiesPanel } from "@/components/providers/ProviderSpecialtiesPanel"
import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({
  listCatalogue: vi.fn(),
  listLinks: vi.fn(),
  link: vi.fn(),
  unlink: vi.fn(),
  canWrite: true,
}))
vi.mock("@/api/endpoints/provider-specialties", () => ({ providerSpecialtiesApi: mocks }))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => mocks.canWrite,
  useCurrentRole: () => "Admin",
}))

const TRAUMA = {
  id: "lnk-1",
  tenant_id: "tenant-1",
  provider_id: "prv-1",
  specialty_id: "spc-1",
  specialty_code: "TRAUMA",
  specialty_label: "Trauma",
  specialty_is_active: true,
}
const RETIRED = {
  ...TRAUMA,
  id: "lnk-2",
  specialty_id: "spc-9",
  specialty_code: "OLD",
  specialty_label: "Legacy counselling",
  specialty_is_active: false,
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.canWrite = true
  mocks.listLinks.mockResolvedValue([TRAUMA])
  mocks.listCatalogue.mockResolvedValue([
    { id: "spc-1", code: "TRAUMA", label: "Trauma", is_active: true },
    { id: "spc-2", code: "SUBST", label: "Substance use", is_active: true },
  ])
  mocks.link.mockResolvedValue(TRAUMA)
  mocks.unlink.mockResolvedValue(undefined)
})

describe("practitioner specialties", () => {
  it("reads specialties from the catalogue links, not from free text", async () => {
    renderWithProviders(<ProviderSpecialtiesPanel providerId="prv-1" />)
    expect(await screen.findByText("Trauma")).toBeInTheDocument()
    expect(mocks.listLinks).toHaveBeenCalledWith("prv-1")
  })

  it("keeps a link to a retired specialty visible and marks it retired", async () => {
    mocks.listLinks.mockResolvedValue([TRAUMA, RETIRED])
    renderWithProviders(<ProviderSpecialtiesPanel providerId="prv-1" />)
    expect(await screen.findByText("Legacy counselling")).toBeInTheDocument()
    expect(screen.getByText("RETIRED")).toBeInTheDocument()
  })

  it("does not offer a retired entry for new selection", async () => {
    mocks.listCatalogue.mockResolvedValue([
      { id: "spc-2", code: "SUBST", label: "Substance use", is_active: true },
    ])
    const user = userEvent.setup()
    renderWithProviders(<ProviderSpecialtiesPanel providerId="prv-1" />)
    await screen.findByText("Trauma")

    // The catalogue request asks for active entries only.
    expect(mocks.listCatalogue).toHaveBeenCalledWith()
    await user.click(screen.getByRole("combobox", { name: /add a specialty/i }))
    expect(await screen.findByRole("option", { name: "Substance use" })).toBeInTheDocument()
    expect(screen.queryByRole("option", { name: "Legacy counselling" })).not.toBeInTheDocument()
  })

  it("omits an already-linked specialty from the picker", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProviderSpecialtiesPanel providerId="prv-1" />)
    await screen.findByText("Trauma")
    await user.click(screen.getByRole("combobox", { name: /add a specialty/i }))
    expect(await screen.findByRole("option", { name: "Substance use" })).toBeInTheDocument()
    expect(screen.queryByRole("option", { name: "Trauma" })).not.toBeInTheDocument()
  })

  it("links by catalogue id", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProviderSpecialtiesPanel providerId="prv-1" />)
    await screen.findByText("Trauma")
    await user.click(screen.getByRole("combobox", { name: /add a specialty/i }))
    await user.click(await screen.findByRole("option", { name: "Substance use" }))
    fireEvent.click(screen.getByRole("button", { name: /add specialty/i }))

    await waitFor(() => expect(mocks.link).toHaveBeenCalledWith("prv-1", "spc-2"))
  })

  it("gives a viewer no add or remove control", async () => {
    mocks.canWrite = false
    renderWithProviders(<ProviderSpecialtiesPanel providerId="prv-1" />)
    await screen.findByText("Trauma")
    expect(screen.queryByRole("button", { name: /add specialty/i })).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /remove trauma/i })).not.toBeInTheDocument()
  })
})
