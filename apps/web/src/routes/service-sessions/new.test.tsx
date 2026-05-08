import { fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactElement } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/utils'
import { ApiError } from '@/types/api'

const createMock = vi.fn()
const navigateMock = vi.fn()

vi.mock('@/api/endpoints/service-sessions', () => ({
  serviceSessionsApi: {
    create: (...args: unknown[]) => createMock(...args),
  },
}))

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )
  return {
    ...actual,
    useNavigate: () => navigateMock,
    createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  }
})

beforeEach(() => {
  createMock.mockReset()
  navigateMock.mockReset()
})
afterEach(() => {
  createMock.mockReset()
  navigateMock.mockReset()
})

async function importPage() {
  const mod = await import('@/routes/service-sessions/new')
  return mod
}

describe('service-sessions/new — ServiceSessionCreatePage', () => {
  it('rejects empty submission with field errors', async () => {
    const { Route } = await importPage()
    const Page = (Route.options.component ?? (() => null)) as () => ReactElement | null
    renderWithProviders(<Page />)

    fireEvent.click(screen.getByRole('button', { name: /create session/i }))
    expect(await screen.findByText(/service id is required/i)).toBeInTheDocument()
    expect(screen.getByText(/person id is required/i)).toBeInTheDocument()
    expect(screen.getByText(/scheduled time is required/i)).toBeInTheDocument()
    expect(createMock).not.toHaveBeenCalled()
  })

  it('converts datetime-local input to ISO before submit', async () => {
    createMock.mockResolvedValue({ id: 'sess-1' })
    const user = userEvent.setup()
    const { Route } = await importPage()
    const Page = (Route.options.component ?? (() => null)) as () => ReactElement | null
    renderWithProviders(<Page />)

    await user.type(screen.getByLabelText(/service id/i), 'svc-1')
    await user.type(screen.getByLabelText(/person id/i), 'p-1')
    fireEvent.change(screen.getByLabelText(/scheduled at/i), {
      target: { value: '2026-06-01T10:30' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create session/i }))

    await waitFor(() => expect(createMock).toHaveBeenCalled())
    const args = createMock.mock.calls[0][0]
    expect(args.service_id).toBe('svc-1')
    expect(args.person_id).toBe('p-1')
    expect(args.scheduled_at).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)
  })

  it('navigates to the list on success', async () => {
    createMock.mockResolvedValue({ id: 'sess-1' })
    const user = userEvent.setup()
    const { Route } = await importPage()
    const Page = (Route.options.component ?? (() => null)) as () => ReactElement | null
    renderWithProviders(<Page />)

    await user.type(screen.getByLabelText(/service id/i), 's')
    await user.type(screen.getByLabelText(/person id/i), 'p')
    fireEvent.change(screen.getByLabelText(/scheduled at/i), {
      target: { value: '2026-06-01T10:30' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create session/i }))

    await waitFor(() =>
      expect(navigateMock).toHaveBeenCalledWith(
        expect.objectContaining({ to: '/service-sessions' }),
      ),
    )
  })

  it('maps server fieldErrors to fields', async () => {
    createMock.mockRejectedValue(
      new ApiError('Bad', 'VALIDATION', 422, { service_id: 'Service not found' }),
    )
    const user = userEvent.setup()
    const { Route } = await importPage()
    const Page = (Route.options.component ?? (() => null)) as () => ReactElement | null
    renderWithProviders(<Page />)

    await user.type(screen.getByLabelText(/service id/i), 'bogus')
    await user.type(screen.getByLabelText(/person id/i), 'p')
    fireEvent.change(screen.getByLabelText(/scheduled at/i), {
      target: { value: '2026-06-01T10:30' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create session/i }))

    expect(await screen.findByText(/service not found/i)).toBeInTheDocument()
  })
})
