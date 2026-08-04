/**
 * Happy path for the persons list: rows render as people (names), never as
 * raw identifiers — the exact regression this table shipped with once.
 */

import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/utils'

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

vi.mock('@/api/endpoints/persons', () => ({
  personsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'p_1',
          first_name: 'Janet',
          last_name: 'Nakato',
          person_type: 'ClientEmployee',
          status: 'Active',
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
  clientsApi: { list: vi.fn().mockResolvedValue({ items: [], total: 0 }) },
}))
vi.mock('@/api/endpoints/users', () => ({
  usersApi: { getById: vi.fn() },
}))

const { Route } = await import('@/routes/persons/index')
const Page = (Route as unknown as { options: { component: React.ComponentType } })
  .options.component

describe('persons list — happy path', () => {
  it('renders the person by name, not by identifier', async () => {
    const screen = renderWithProviders(<Page />)
    expect(await screen.findByText('Janet Nakato')).toBeInTheDocument()
    expect(screen.queryByText('p_1')).not.toBeInTheDocument()
  })
})
