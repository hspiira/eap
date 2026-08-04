import { screen } from '@testing-library/react'
import { Users } from 'lucide-react'
import { describe, expect, it, vi } from 'vitest'

import { renderDetailState } from '@/components/common/DetailStates'
import { renderWithProviders } from '@/test/utils'
import { ApiError } from '@/types/api'

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children }: { children: React.ReactNode }) => <a>{children}</a>,
}))

const PROPS = {
  icon: Users,
  breadcrumb: 'People · Persons',
  entity: 'person',
  backTo: vi.fn(),
  backLabel: 'Back to persons',
}

function query(overrides: Partial<Parameters<typeof renderDetailState>[0]>) {
  return {
    isPending: false,
    isError: false,
    error: null,
    data: null,
    refetch: vi.fn(),
    ...overrides,
  }
}

describe('renderDetailState', () => {
  it('renders the entity (returns null) once data has loaded', () => {
    expect(renderDetailState(query({ data: { id: 'p1' } }), PROPS)).toBeNull()
  })

  it('shows a skeleton while pending', () => {
    const el = renderDetailState(query({ isPending: true }), PROPS)
    expect(el).not.toBeNull()
  })

  describe('a 404 means the record does not exist', () => {
    it('renders not-found', () => {
      const err = new ApiError('Not found', 'NOT_FOUND', 404)
      const el = renderDetailState(query({ isError: true, error: err }), PROPS)
      renderWithProviders(el)
      expect(screen.getByText('Person not found')).toBeInTheDocument()
    })

    it('offers a way back, not a retry', () => {
      const err = new ApiError('Not found', 'NOT_FOUND', 404)
      renderWithProviders(renderDetailState(query({ isError: true, error: err }), PROPS))
      expect(screen.getByText('Back to persons')).toBeInTheDocument()
      expect(screen.queryByText('Try again')).not.toBeInTheDocument()
    })
  })

  describe('any other failure is not a missing record', () => {
    /**
     * The regression: these pages used to catch every error into a null entity
     * and render "not found", so an outage told the user their data was gone.
     */
    it.each([
      ['a 500', new ApiError('Server error', 'SERVER_ERROR', 500)],
      ['a network failure', new ApiError('Network error', 'NETWORK_ERROR', 0)],
      ['a timeout', new ApiError('Timed out', 'TIMEOUT', 0)],
      ['a 403', new ApiError('Forbidden', 'FORBIDDEN', 403)],
    ])('does not claim the person is missing on %s', (_label, err) => {
      renderWithProviders(renderDetailState(query({ isError: true, error: err }), PROPS))
      expect(screen.queryByText('Person not found')).not.toBeInTheDocument()
      expect(screen.getByText(/Couldn't load this person/)).toBeInTheDocument()
    })

    it('offers a retry', () => {
      const err = new ApiError('Server error', 'SERVER_ERROR', 500)
      renderWithProviders(renderDetailState(query({ isError: true, error: err }), PROPS))
      expect(screen.getByText('Try again')).toBeInTheDocument()
    })

    it('surfaces the reason rather than a generic message', () => {
      const err = new ApiError('Upstream timeout', 'SERVER_ERROR', 503)
      renderWithProviders(renderDetailState(query({ isError: true, error: err }), PROPS))
      expect(screen.getByText('Upstream timeout')).toBeInTheDocument()
    })
  })

  it('treats a successful-but-empty response as not-found', () => {
    renderWithProviders(renderDetailState(query({ data: null }), PROPS))
    expect(screen.getByText('Person not found')).toBeInTheDocument()
  })
})
