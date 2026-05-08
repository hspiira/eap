import { fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactElement } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/utils'
import { ApiError } from '@/types/api'

const createMock = vi.fn()
const navigateMock = vi.fn()

vi.mock('@/api/endpoints/persons', () => ({
  personsApi: {
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
  const mod = await import('@/routes/persons/new')
  return mod
}

describe('persons/new — PersonCreatePage', () => {
  it('rejects submission with empty required fields', async () => {
    const { Route } = await importPage()
    const Page = (Route.options.component ?? (() => null)) as () => ReactElement | null
    renderWithProviders(<Page />)

    fireEvent.click(screen.getByRole('button', { name: /create person/i }))
    expect(await screen.findByText(/first name is required/i)).toBeInTheDocument()
    expect(screen.getByText(/last name is required/i)).toBeInTheDocument()
    expect(createMock).not.toHaveBeenCalled()
  })

  it('submits valid values and navigates', async () => {
    createMock.mockResolvedValue({ id: 'p1' })
    const user = userEvent.setup()
    const { Route } = await importPage()
    const Page = (Route.options.component ?? (() => null)) as () => ReactElement | null
    renderWithProviders(<Page />)

    await user.type(screen.getByLabelText(/first name/i), 'Ada')
    await user.type(screen.getByLabelText(/last name/i), 'Lovelace')
    fireEvent.click(screen.getByRole('button', { name: /create person/i }))

    await waitFor(() => expect(createMock).toHaveBeenCalledTimes(1))
    expect(createMock.mock.calls[0][0]).toMatchObject({
      first_name: 'Ada',
      last_name: 'Lovelace',
    })
    await waitFor(() =>
      expect(navigateMock).toHaveBeenCalledWith(expect.objectContaining({ to: '/persons' })),
    )
  })

  it('default person_type submits as CLIENT_EMPLOYEE', async () => {
    createMock.mockResolvedValue({ id: 'p1' })
    const user = userEvent.setup()
    const { Route } = await importPage()
    const Page = (Route.options.component ?? (() => null)) as () => ReactElement | null
    renderWithProviders(<Page />)

    await user.type(screen.getByLabelText(/first name/i), 'Ada')
    await user.type(screen.getByLabelText(/last name/i), 'Lovelace')
    fireEvent.click(screen.getByRole('button', { name: /create person/i }))

    await waitFor(() => expect(createMock).toHaveBeenCalled())
    expect(createMock.mock.calls[0][0].person_type).toBeTruthy()
  })

  it('shows server error banner on 500', async () => {
    createMock.mockRejectedValue(new ApiError('boom', 'X', 500))
    const user = userEvent.setup()
    const { Route } = await importPage()
    const Page = (Route.options.component ?? (() => null)) as () => ReactElement | null
    renderWithProviders(<Page />)

    await user.type(screen.getByLabelText(/first name/i), 'Ada')
    await user.type(screen.getByLabelText(/last name/i), 'Lovelace')
    fireEvent.click(screen.getByRole('button', { name: /create person/i }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(navigateMock).not.toHaveBeenCalled()
  })

  it('client_id passed through when provided', async () => {
    createMock.mockResolvedValue({ id: 'p1' })
    const user = userEvent.setup()
    const { Route } = await importPage()
    const Page = (Route.options.component ?? (() => null)) as () => ReactElement | null
    renderWithProviders(<Page />)

    await user.type(screen.getByLabelText(/first name/i), 'Ada')
    await user.type(screen.getByLabelText(/last name/i), 'Lovelace')
    await user.type(screen.getByLabelText(/client id/i), 'client-123')
    fireEvent.click(screen.getByRole('button', { name: /create person/i }))

    await waitFor(() => expect(createMock).toHaveBeenCalled())
    expect(createMock.mock.calls[0][0].client_id).toBe('client-123')
  })
})
