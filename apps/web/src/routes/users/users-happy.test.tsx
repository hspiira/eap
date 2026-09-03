/** Happy path for the users list: rows appear with email and role. */

import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/utils'

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

vi.mock('@/api/endpoints/users', () => ({
  usersApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'u_1',
          email: 'counsellor@minet.co.ug',
          status: 'Active',
          role: 'User',
          is_email_verified: true,
          is_two_factor_enabled: false,
          is_active: true,
          auth_provider: 'password',
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

const { Route } = await import('@/routes/users/index')
const Page = (Route as unknown as { options: { component: React.ComponentType } })
  .options.component

describe('users list — happy path', () => {
  it('renders the user row by email', async () => {
    const screen = renderWithProviders(<Page />)
    expect(await screen.findByText('counsellor@minet.co.ug')).toBeInTheDocument()
  })
})
