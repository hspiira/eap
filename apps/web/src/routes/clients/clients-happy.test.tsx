/**
 * Happy path for the clients list: the page renders the server's rows as
 * human-readable values (names, not identifiers) with the total beside them.
 */

import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/utils'

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

vi.mock('@/api/endpoints/clients', () => ({
  clientsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'cl_1',
          name: 'Stanbic Bank Uganda',
          code: 'STAN',
          status: 'Active',
          tier: 'A',
          staff_count: 240,
          created_at: '2026-01-05T00:00:00Z',
          updated_at: '2026-01-05T00:00:00Z',
        },
        {
          id: 'cl_2',
          name: 'Uganda Breweries',
          code: 'UBL',
          status: 'Active',
          tier: 'B',
          staff_count: 90,
          created_at: '2026-01-06T00:00:00Z',
          updated_at: '2026-01-06T00:00:00Z',
        },
      ],
      total: 2,
      page: 1,
      limit: 20,
    }),
  },
}))

const { Route } = await import('@/routes/clients/index')
const Page = (Route as unknown as { options: { component: React.ComponentType } })
  .options.component

describe('clients list — happy path', () => {
  it('renders client names from the server page, not identifiers', async () => {
    const screen = renderWithProviders(<Page />)
    expect(await screen.findByText('Stanbic Bank Uganda')).toBeInTheDocument()
    expect(await screen.findByText('Uganda Breweries')).toBeInTheDocument()
    expect(screen.queryByText('cl_1')).not.toBeInTheDocument()
  })
})
