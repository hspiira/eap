/** Happy path for the services list: rows appear by service name. */

import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/utils'

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

vi.mock('@/api/endpoints/services', () => ({
  servicesApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'sv_1',
          name: 'Short-term counselling',
          status: 'Active',
          is_group_service: false,
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

const { Route } = await import('@/routes/services/index')
const Page = (Route as unknown as { options: { component: React.ComponentType } })
  .options.component

describe('services list — happy path', () => {
  it('renders the service by name', async () => {
    const screen = renderWithProviders(<Page />)
    expect(await screen.findByText('Short-term counselling')).toBeInTheDocument()
  })
})
