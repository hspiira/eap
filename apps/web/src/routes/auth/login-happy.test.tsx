/**
 * Happy path for the login page: both entry points render — the Microsoft
 * SSO button and the password fallback — matching the Option C UX.
 */

import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/utils'

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({
    options: opts,
    useSearch: () => ({}),
  }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

vi.mock('@/api/endpoints/auth', () => ({
  authApi: {
    isAzureSsoEnabled: () => true,
    login: vi.fn(),
    getAzureLoginUrl: () => 'http://localhost:8000/auth/azure/login',
  },
}))
vi.mock('@/hooks/useRedirectIfAuthenticated', () => ({
  useRedirectIfAuthenticated: () => false,
}))

const { Route } = await import('@/routes/auth/login')
const Page = (Route as unknown as { options: { component: React.ComponentType } })
  .options.component

describe('login — happy path', () => {
  it('offers Microsoft SSO and the password fallback', async () => {
    const screen = renderWithProviders(<Page />)
    expect(await screen.findByText(/Sign in with Microsoft/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^Password/)).toBeInTheDocument()
  })
})
