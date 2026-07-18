/**
 * Happy path for the contracts list: the client column shows the client's
 * name resolved from the lookup, not a truncated id, and the term renders
 * from the wire-true period object.
 */

import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/utils'

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

vi.mock('@/api/endpoints/contracts', () => ({
  contractsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'ct_1',
          client_id: 'cl_1',
          status: 'Active',
          period: {
            start_date: '2026-01-01T00:00:00Z',
            end_date: '2026-12-31T00:00:00Z',
            duration_months: 12,
          },
          billing_rate: { amount: '2500000.00', currency: 'KES' },
          payment_frequency: 'Monthly',
          payment_status: 'Paid',
          is_auto_renew: true,
          is_active: true,
          days_remaining: 200,
          created_at: '2026-01-05T00:00:00Z',
          updated_at: '2026-01-05T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      limit: 20,
    }),
  },
}))
vi.mock('@/api/endpoints/clients', () => ({
  clientsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'cl_1',
          name: 'Stanbic Bank Uganda',
          status: 'Active',
          created_at: '2026-01-05T00:00:00Z',
          updated_at: '2026-01-05T00:00:00Z',
        },
      ],
      total: 1,
    }),
  },
}))

const { Route } = await import('@/routes/contracts/index')
const Page = (Route as unknown as { options: { component: React.ComponentType } })
  .options.component

describe('contracts list — happy path', () => {
  it('resolves the client name instead of showing an id fragment', async () => {
    const screen = renderWithProviders(<Page />)
    expect(await screen.findByText('Stanbic Bank Uganda')).toBeInTheDocument()
    expect(screen.queryByText('cl_1')).not.toBeInTheDocument()
  })
})
