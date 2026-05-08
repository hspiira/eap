import { screen } from '@testing-library/react'
import type { ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/utils'

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )
  return {
    ...actual,
    Link: ({ children }: { children: React.ReactNode }) => <a>{children}</a>,
    createFileRoute: () => (opts: Record<string, unknown>) => ({
      options: opts,
      useParams: () => ({ templateSlug: 'per-client-renewal' }),
    }),
  }
})

async function renderRoute(modulePath: string): Promise<HTMLElement> {
  const mod = (await import(/* @vite-ignore */ modulePath)) as {
    Route: { options: { component?: () => ReactElement | null } }
  }
  const Page = (mod.Route.options.component ?? (() => null)) as () => ReactElement | null
  const { container } = renderWithProviders(<Page />)
  return container
}

describe('reports landing', () => {
  it('lists the four report templates', async () => {
    await renderRoute('@/routes/reports/index')
    expect(screen.getByText(/per-client renewal pack/i)).toBeInTheDocument()
    expect(screen.getByText(/care callback wave summary/i)).toBeInTheDocument()
    expect(screen.getByText(/tier-portfolio snapshot/i)).toBeInTheDocument()
    expect(screen.getByText(/anchor-cohort benchmark/i)).toBeInTheDocument()
  })

  it('marks not-yet-implemented templates as coming soon', async () => {
    await renderRoute('@/routes/reports/index')
    expect(screen.getAllByText(/coming soon/i).length).toBeGreaterThanOrEqual(3)
  })
})

describe('per-client renewal pack template', () => {
  it('renders all sections from the fixture', async () => {
    await renderRoute('@/routes/reports/$templateSlug')

    expect(screen.getAllByText(/stanbic bank kenya/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/sessions delivered by month/i)).toBeInTheDocument()
    expect(screen.getByText(/diagnosis prevalence/i)).toBeInTheDocument()
    expect(screen.getByText(/care-callback outcomes/i)).toBeInTheDocument()
    expect(screen.getByText(/satisfaction distribution/i)).toBeInTheDocument()
  })

  it('shows period and tier in the header', async () => {
    await renderRoute('@/routes/reports/$templateSlug')
    expect(screen.getByText(/jun 2025 .* may 2026/i)).toBeInTheDocument()
    expect(screen.getByText('Tier A')).toBeInTheDocument()
  })

  it('renders a print button', async () => {
    await renderRoute('@/routes/reports/$templateSlug')
    expect(screen.getByRole('button', { name: /print/i })).toBeInTheDocument()
  })
})
