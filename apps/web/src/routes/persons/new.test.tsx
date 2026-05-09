import { fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { PersonFormSheet } from '@/components/PersonFormSheet'
import { renderWithProviders } from '@/test/utils'
import { ApiError } from '@/types/api'

const createMock = vi.fn()
const listClientsMock = vi.fn().mockResolvedValue({ items: [], total: 0 })
const listPersonsMock = vi.fn().mockResolvedValue({ items: [], total: 0 })

vi.mock('@/api/endpoints/persons', () => ({
  personsApi: {
    create: (...args: unknown[]) => createMock(...args),
    list: (...args: unknown[]) => listPersonsMock(...args),
  },
}))

vi.mock('@/api/endpoints/clients', () => ({
  clientsApi: {
    list: (...args: unknown[]) => listClientsMock(...args),
  },
}))

beforeEach(() => {
  createMock.mockReset()
  listClientsMock.mockClear()
  listPersonsMock.mockClear()
})
afterEach(() => {
  createMock.mockReset()
})

describe('PersonFormSheet — create', () => {
  it('rejects submission with empty required fields', async () => {
    renderWithProviders(<PersonFormSheet open onOpenChange={() => {}} />)

    fireEvent.click(screen.getByRole('button', { name: /create person/i }))
    expect(await screen.findByText(/first name is required/i)).toBeInTheDocument()
    expect(screen.getByText(/last name is required/i)).toBeInTheDocument()
    expect(createMock).not.toHaveBeenCalled()
  })

  it('client_id is required for ClientEmployee role', async () => {
    renderWithProviders(<PersonFormSheet open onOpenChange={() => {}} />)

    fireEvent.change(screen.getByLabelText(/first name/i), { target: { value: 'Ada' } })
    fireEvent.change(screen.getByLabelText(/last name/i), { target: { value: 'Lovelace' } })
    fireEvent.click(screen.getByRole('button', { name: /create person/i }))

    expect(
      await screen.findByText(/client is required for employees/i),
    ).toBeInTheDocument()
    expect(createMock).not.toHaveBeenCalled()
  })

  it('submits valid values when client is locked', async () => {
    createMock.mockResolvedValue({ id: 'p1', first_name: 'Ada', last_name: 'Lovelace' })
    const onSaved = vi.fn()
    const onOpenChange = vi.fn()
    renderWithProviders(
      <PersonFormSheet
        open
        onOpenChange={onOpenChange}
        clientId="client-123"
        client={{
          id: 'client-123',
          name: 'Acme Corp',
          code: 'ACME',
        } as never}
        onSaved={onSaved}
      />,
    )

    fireEvent.change(screen.getByLabelText(/first name/i), { target: { value: 'Ada' } })
    fireEvent.change(screen.getByLabelText(/last name/i), { target: { value: 'Lovelace' } })
    fireEvent.click(screen.getByRole('button', { name: /create person/i }))

    await waitFor(() => expect(createMock).toHaveBeenCalledTimes(1))
    expect(createMock.mock.calls[0][0]).toMatchObject({
      first_name: 'Ada',
      last_name: 'Lovelace',
      client_id: 'client-123',
    })
    await waitFor(() => expect(onSaved).toHaveBeenCalled())
  })

  it('shows server error banner on 500', async () => {
    createMock.mockRejectedValue(new ApiError('boom', 'X', 500))
    renderWithProviders(
      <PersonFormSheet
        open
        onOpenChange={() => {}}
        clientId="client-123"
        client={{ id: 'client-123', name: 'Acme', code: 'ACME' } as never}
      />,
    )

    fireEvent.change(screen.getByLabelText(/first name/i), { target: { value: 'Ada' } })
    fireEvent.change(screen.getByLabelText(/last name/i), { target: { value: 'Lovelace' } })
    fireEvent.click(screen.getByRole('button', { name: /create person/i }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })
})
