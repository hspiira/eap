import { screen } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"
import type { Contract } from "@/types/entities"
import { PricingModel } from "@/types/enums"

import { ContractBillingPanel } from "./ContractBillingPanel"

const mocks = vi.hoisted(() => ({
  invoicePreview: vi.fn(),
  events: vi.fn(),
  listServices: vi.fn(),
}))
vi.mock("@/api/endpoints/pricing", () => ({ pricingApi: { invoicePreview: mocks.invoicePreview } }))
vi.mock("@/api/endpoints/utilisation", () => ({ utilisationApi: { byContract: mocks.events } }))
vi.mock("@/api/endpoints/services", () => ({ servicesApi: { list: mocks.listServices } }))

function makeContract(overrides: Partial<Contract> = {}): Contract {
  return {
    id: "contract-1",
    tenant_id: "tenant-1",
    client_id: "client-1",
    status: "Active",
    period: { start_date: "2026-01-01", end_date: "2026-12-31" },
    billing_rate: { amount: 100, currency: "UGX" },
    pricing_model: PricingModel.FEE_FOR_SERVICE,
    payment_frequency: "Monthly",
    payment_status: "Paid",
    is_auto_renew: false,
    is_active: true,
    days_remaining: 100,
    last_billing_date: "2026-08-01",
    next_billing_date: "2026-08-31",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  } as Contract
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.events.mockResolvedValue([])
  mocks.listServices.mockResolvedValue({ items: [], total: 0, page: 1, limit: 200, has_more: false })
  mocks.invoicePreview.mockResolvedValue({
    contract_id: "contract-1",
    period_from: "2026-08-01",
    period_to: "2026-08-31",
    pricing_model: PricingModel.FEE_FOR_SERVICE,
    currency: "UGX",
    lines: [
      {
        description: "Individual Counselling",
        quantity: 3,
        unit_amount: { amount: "120000", currency: "UGX" },
        total: { amount: "360000", currency: "UGX" },
      },
    ],
    subtotal: { amount: "360000", currency: "UGX" },
    notes: [],
  })
})

describe("contract billing", () => {
  it("puts an amount against each billed line and a subtotal on the window", async () => {
    renderWithProviders(<ContractBillingPanel contract={makeContract()} />)

    expect(await screen.findByText("Individual Counselling")).toBeInTheDocument()
    expect(screen.getByText("UGX 120,000")).toBeInTheDocument()
    expect(screen.getAllByText("UGX 360,000").length).toBeGreaterThan(0)
  })

  it("prices the contract's own billing window by default", async () => {
    renderWithProviders(<ContractBillingPanel contract={makeContract()} />)
    await screen.findByText("Individual Counselling")
    expect(mocks.invoicePreview).toHaveBeenCalledWith("contract-1", {
      period_from: "2026-08-01",
      period_to: "2026-08-31",
    })
  })

  it("says why a window cannot be priced rather than showing an empty invoice", async () => {
    renderWithProviders(<ContractBillingPanel contract={makeContract({ pricing_model: null })} />)
    expect(await screen.findByText(/no pricing configuration/)).toBeInTheDocument()
    expect(mocks.invoicePreview).not.toHaveBeenCalled()
  })

  it("reports a pricing failure instead of implying nothing is owed", async () => {
    mocks.invoicePreview.mockRejectedValue(new Error("Contract has no pricing configuration"))
    renderWithProviders(<ContractBillingPanel contract={makeContract()} />)
    expect(await screen.findByRole("alert")).toBeInTheDocument()
  })
})
