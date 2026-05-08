import { fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ClientForm } from '@/components/ClientForm'
import { renderWithProviders } from '@/test/utils'
import { ApiError } from '@/types/api'

const createMock = vi.fn()
vi.mock('@/api/endpoints/clients', () => ({
  clientsApi: {
    create: (...args: unknown[]) => createMock(...args),
  },
}))

beforeEach(() => createMock.mockReset())
afterEach(() => createMock.mockReset())

describe('ClientForm', () => {
  it('rejects empty submission with field errors', async () => {
    renderWithProviders(<ClientForm />)
    fireEvent.click(screen.getByRole('button', { name: /create client/i }))

    expect(await screen.findByText(/name is required/i)).toBeInTheDocument()
    expect(screen.getByText(/code must be 3.5 characters/i)).toBeInTheDocument()
    expect(createMock).not.toHaveBeenCalled()
  })

  it('rejects code shorter than 3 chars', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ClientForm />)

    await user.type(screen.getByLabelText(/^name/i), 'Acme')
    await user.type(screen.getByLabelText(/^code/i), 'AB')
    fireEvent.click(screen.getByRole('button', { name: /create client/i }))

    expect(await screen.findByText(/code must be 3.5 characters/i)).toBeInTheDocument()
    expect(createMock).not.toHaveBeenCalled()
  })

  it('submits valid values to clientsApi.create', async () => {
    createMock.mockResolvedValue({ id: 'c1', name: 'Acme' })
    const onSuccess = vi.fn()
    const user = userEvent.setup()

    renderWithProviders(<ClientForm onSuccess={onSuccess} />)

    await user.type(screen.getByLabelText(/^name/i), 'Acme')
    await user.type(screen.getByLabelText(/^code/i), 'ACM')
    await user.type(screen.getByLabelText(/email/i), 'a@b.com')
    fireEvent.click(screen.getByRole('button', { name: /create client/i }))

    await waitFor(() => expect(createMock).toHaveBeenCalledTimes(1))
    expect(createMock.mock.calls[0][0]).toEqual({
      name: 'Acme',
      code: 'ACM',
      contact_info: { email: 'a@b.com', phone: undefined },
    })
    await waitFor(() => expect(onSuccess).toHaveBeenCalled())
  })

  it('maps server fieldErrors to fields', async () => {
    createMock.mockRejectedValue(
      new ApiError('Bad', 'VALIDATION', 422, { name: 'Already exists' }),
    )
    const user = userEvent.setup()

    renderWithProviders(<ClientForm />)
    await user.type(screen.getByLabelText(/^name/i), 'Acme')
    await user.type(screen.getByLabelText(/^code/i), 'ACM')
    fireEvent.click(screen.getByRole('button', { name: /create client/i }))

    expect(await screen.findByText(/already exists/i)).toBeInTheDocument()
  })

  it('shows non-field server errors as a banner', async () => {
    createMock.mockRejectedValue(new ApiError('Internal boom', 'X', 500))
    const user = userEvent.setup()

    renderWithProviders(<ClientForm />)
    await user.type(screen.getByLabelText(/^name/i), 'Acme')
    await user.type(screen.getByLabelText(/^code/i), 'ACM')
    fireEvent.click(screen.getByRole('button', { name: /create client/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/server error/i)
  })

  it('rejects malformed email', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ClientForm />)

    await user.type(screen.getByLabelText(/^name/i), 'Acme')
    await user.type(screen.getByLabelText(/^code/i), 'ACM')
    await user.type(screen.getByLabelText(/email/i), 'not-an-email')
    fireEvent.click(screen.getByRole('button', { name: /create client/i }))

    expect(await screen.findByText(/invalid email/i)).toBeInTheDocument()
    expect(createMock).not.toHaveBeenCalled()
  })

  it('cancel button calls onCancel', () => {
    const onCancel = vi.fn()
    renderWithProviders(<ClientForm onCancel={onCancel} />)
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onCancel).toHaveBeenCalled()
  })

  it('submit button shows loading text while pending', async () => {
    let resolve: (v: unknown) => void = () => {}
    createMock.mockImplementation(() => new Promise((r) => (resolve = r)))
    const user = userEvent.setup()

    renderWithProviders(<ClientForm />)
    await user.type(screen.getByLabelText(/^name/i), 'Acme')
    await user.type(screen.getByLabelText(/^code/i), 'ACM')
    fireEvent.click(screen.getByRole('button', { name: /create client/i }))

    expect(await screen.findByRole('button', { name: /creating/i })).toBeDisabled()
    resolve({ id: 'c1', name: 'Acme' })
  })
})
