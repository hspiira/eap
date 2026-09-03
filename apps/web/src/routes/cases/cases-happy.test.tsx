/**
 * Happy path for the cases list: rows render the case's pseudonymous
 * subject reference (never a name — Case only carries clinical_subject_id
 * by design, the privacy wall), and the route is gated on Clinical scope.
 */

import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/utils'

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

vi.mock('@/api/endpoints/cases', () => ({
  casesApi: {
    list: vi.fn().mockResolvedValue([
      {
        id: 'case_1',
        tenant_id: 't1',
        clinical_subject_id: 'cs_ab12cd34ef56',
        client_id: 'cl_1',
        presenting_problem: 'Stress',
        referral_source: 'Self',
        status: 'Intake',
        opened_at: '2026-01-05T00:00:00Z',
        assigned_counsellor_id: null,
        authorization_id: null,
        referred_by_user_id: null,
        referral_notes: null,
        closed_at: null,
        closure_reason: null,
        closure_summary_note_id: null,
        intake_screener_admin_ids: [],
        closure_screener_admin_ids: [],
        created_at: '2026-01-05T00:00:00Z',
        updated_at: '2026-01-05T00:00:00Z',
      },
    ]),
  },
}))

// This test covers the list rendering, not the auth/scope gate — those are
// their own concern. Render children directly, the way the other happy-path
// tests exercise their (ungated) list pages.
vi.mock('@/components/common/RequireClinicalScope', () => ({
  RequireClinicalScope: ({ children }: { children?: React.ReactNode }) => children,
}))

const { Route } = await import('@/routes/cases/index')
const Page = (Route as unknown as { options: { component: React.ComponentType } })
  .options.component

describe('cases list — happy path', () => {
  it('renders the case by its subject reference, not a name', async () => {
    const screen = renderWithProviders(<Page />)
    expect(await screen.findByText('cs_ab12cd34ef56')).toBeInTheDocument()
    expect(await screen.findByText('Open case')).toBeInTheDocument()
  })
})
