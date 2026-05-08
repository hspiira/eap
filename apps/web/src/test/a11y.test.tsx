/**
 * A11y gate. Renders each gated route's form and asserts zero serious/critical
 * axe-core issues. Pairs with the keyboard-walkthrough manual QA in Phase 1 #5.
 */

import type { ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { configureAxe } from 'vitest-axe'

import { ClientForm } from '@/components/ClientForm'
import { renderWithProviders } from '@/test/utils'

const axe = configureAxe({
  rules: {
    'color-contrast': { enabled: false },
    region: { enabled: false },
  },
})

vi.mock('@/api/endpoints/clients', () => ({
  clientsApi: { create: vi.fn() },
}))
vi.mock('@/api/endpoints/persons', () => ({
  personsApi: { create: vi.fn() },
}))
vi.mock('@/api/endpoints/service-sessions', () => ({
  serviceSessionsApi: { create: vi.fn() },
}))
vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  }
})

async function renderRoutePage(modulePath: string): Promise<HTMLElement> {
  const mod = (await import(/* @vite-ignore */ modulePath)) as {
    Route: { options: { component?: () => ReactElement | null } }
  }
  const Page = (mod.Route.options.component ?? (() => null)) as () => ReactElement | null
  const { container } = renderWithProviders(<Page />)
  return container
}

describe('a11y — gated routes (zero serious/critical issues)', () => {
  it('client-create form is accessible', async () => {
    const { container } = renderWithProviders(<ClientForm />)
    await expect(await axe(container)).toHaveNoViolations()
  })

  it('persons/new is accessible', async () => {
    const container = await renderRoutePage('@/routes/persons/new')
    await expect(await axe(container)).toHaveNoViolations()
  })

  it('service-sessions/new is accessible', async () => {
    const container = await renderRoutePage('@/routes/service-sessions/new')
    await expect(await axe(container)).toHaveNoViolations()
  })
})
