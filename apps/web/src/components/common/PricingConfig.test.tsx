import { useState } from 'react'

import { fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { defaultPricingFor, PricingConfig } from '@/components/common/PricingConfig'
import { renderWithProviders } from '@/test/utils'
import type { ContractPricing } from '@/types/entities'
import { PricingModel } from '@/types/enums'

function Harness({ initial }: { initial: PricingModel }) {
  const [pricing, setPricing] = useState<ContractPricing>(defaultPricingFor(initial))
  return (
    <PricingConfig value={pricing} onChange={setPricing} projectedSessions={10} />
  )
}

describe('PricingConfig — one screen per model + invoice preview', () => {
  it('Retainer: renders monthly fee input and invoice preview', async () => {
    renderWithProviders(<Harness initial={PricingModel.RETAINER} />)
    expect(screen.getByLabelText(/monthly fee/i)).toBeInTheDocument()
    await waitFor(() =>
      expect(screen.getByText(/monthly retainer/i)).toBeInTheDocument(),
    )
  })

  it('Retainer: increasing the fee updates the invoice subtotal', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Harness initial={PricingModel.RETAINER} />)
    const fee = screen.getByLabelText(/monthly fee/i) as HTMLInputElement
    await user.clear(fee)
    await user.type(fee, '50000')
    await waitFor(() => expect(screen.getAllByText('50000.00').length).toBeGreaterThan(0))
  })

  it('Framework: renders deposit drawdown widget', async () => {
    renderWithProviders(<Harness initial={PricingModel.FRAMEWORK} />)
    expect(screen.getByLabelText(/framework deposit drawdown/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^deposit$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/drawdown balance/i)).toBeInTheDocument()
  })

  it('FFS: renders single unit-rate input and ffs preview', async () => {
    renderWithProviders(<Harness initial={PricingModel.FFS} />)
    expect(screen.getByLabelText(/unit rate/i)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText(/sessions delivered/i)).toBeInTheDocument())
  })

  it('Admin+Utilisation: shows the below-floor warning', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Harness initial={PricingModel.ADMIN_UTILISATION} />)
    const floor = screen.getByLabelText(/admin floor/i) as HTMLInputElement
    const adminFee = screen.getByLabelText(/monthly admin fee/i) as HTMLInputElement

    await user.clear(floor)
    await user.type(floor, '10000')
    await user.clear(adminFee)
    await user.type(adminFee, '5000')

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/below the floor/i),
    )
  })

  it('Value-Add: lets the user add bundled services', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Harness initial={PricingModel.VALUE_ADD} />)
    const input = screen.getByPlaceholderText(/CISM/i)
    await user.type(input, 'CISM')
    fireEvent.click(screen.getByRole('button', { name: /^add$/i }))
    expect(screen.getByText('CISM')).toBeInTheDocument()
  })

  it('renders the correct input set per model (re-render harness)', () => {
    const { unmount } = renderWithProviders(<Harness initial={PricingModel.RETAINER} />)
    expect(screen.getByLabelText(/^session cap$/i)).toBeInTheDocument()
    unmount()
    renderWithProviders(<Harness initial={PricingModel.FFS} />)
    expect(screen.queryByLabelText(/^session cap$/i)).not.toBeInTheDocument()
    expect(screen.getByLabelText(/unit rate/i)).toBeInTheDocument()
  })
})
