/**
 * Happy path for the sessions list: the service column resolves to the
 * service's name through the lookup, not an id fragment.
 */

import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/utils'

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

vi.mock('@/api/endpoints/service-sessions', () => ({
  serviceSessionsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'ss_1',
          service_id: 'sv_1',
          person_id: 'p_1',
          status: 'Scheduled',
          session_type: 'Online',
          session_category: 'Individual',
          scheduled_at: '2026-08-01T09:00:00Z',
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
vi.mock('@/api/endpoints/services', () => ({
  servicesApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'sv_1',
          name: 'Short-term counselling',
          status: 'Active',
          created_at: '2026-01-05T00:00:00Z',
          updated_at: '2026-01-05T00:00:00Z',
        },
      ],
      total: 1,
    }),
  },
}))
vi.mock('@/api/endpoints/persons', () => ({
  personsApi: {
    getById: vi.fn().mockResolvedValue({
      id: 'p_1',
      first_name: 'Janet',
      last_name: 'Nakato',
      status: 'Active',
    }),
  },
}))
vi.mock('@/api/endpoints/users', () => ({
  usersApi: { getById: vi.fn() },
}))

const { Route } = await import('@/routes/service-sessions/index')
const Page = (Route as unknown as { options: { component: React.ComponentType } })
  .options.component

describe('sessions list — happy path', () => {
  it('resolves the service name instead of an id fragment', async () => {
    const screen = renderWithProviders(<Page />)
    expect(await screen.findByText('Short-term counselling')).toBeInTheDocument()
    expect(screen.queryByText('sv_1')).not.toBeInTheDocument()
  })
})
