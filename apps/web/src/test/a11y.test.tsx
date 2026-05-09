/**
 * A11y gate. Renders each gated route's form and asserts zero serious/critical
 * axe-core issues. Pairs with the keyboard-walkthrough manual QA in Phase 1 #5.
 */

import { describe, expect, it, vi } from 'vitest'
import { configureAxe } from 'vitest-axe'

import { ClientForm } from '@/components/ClientForm'
import { PersonFormSheet } from '@/components/PersonFormSheet'
import { ServiceSessionFormSheet } from '@/components/ServiceSessionFormSheet'
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
  personsApi: { create: vi.fn(), list: vi.fn().mockResolvedValue({ items: [], total: 0 }) },
}))
vi.mock('@/api/endpoints/service-sessions', () => ({
  serviceSessionsApi: { create: vi.fn() },
}))
vi.mock('@/api/endpoints/services', () => ({
  servicesApi: { list: vi.fn().mockResolvedValue({ items: [], total: 0 }) },
}))
vi.mock('@/api/endpoints/providers', () => ({
  providersApi: { list: vi.fn().mockResolvedValue({ items: [], total: 0 }) },
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

describe('a11y — gated routes (zero serious/critical issues)', () => {
  it('client-create form is accessible', async () => {
    const { container } = renderWithProviders(<ClientForm />)
    await expect(await axe(container)).toHaveNoViolations()
  })

  it('person form sheet is accessible', async () => {
    const { container } = renderWithProviders(
      <PersonFormSheet open onOpenChange={() => {}} />,
    )
    await expect(await axe(container)).toHaveNoViolations()
  })

  it('service session form sheet is accessible', async () => {
    const { container } = renderWithProviders(
      <ServiceSessionFormSheet open onOpenChange={() => {}} />,
    )
    await expect(await axe(container)).toHaveNoViolations()
  })
})
