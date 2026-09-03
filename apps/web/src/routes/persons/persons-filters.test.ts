import { describe, expect, it, vi } from 'vitest'

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: () => null,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

const { Route } = await import('@/routes/persons/index')
const validateSearch = (
  Route as unknown as {
    options: { validateSearch: (s: Record<string, unknown>) => Record<string, unknown> }
  }
).options.validateSearch

/**
 * The persons list used to hold `status` in local component state and filter the
 * fetched page in memory, while rendering the server's unfiltered total beside
 * the survivors. With a filter on and more than one page of data the count was
 * wrong, pagination pointed at rows the filter would never show, and matching
 * people on later pages were unreachable. `search`/`person_type`/`client_id` on
 * the same screen were server-side the whole time.
 *
 * Status is now a URL param sent to the server like the filters beside it.
 * These tests pin the parsing half of that; rejecting an unknown value matters
 * because it reaches the API as a query param.
 */
describe('persons list search params', () => {
  it('keeps a valid status so it can be sent to the server', () => {
    expect(validateSearch({ status: 'Active' })).toEqual({ status: 'Active' })
    expect(validateSearch({ status: 'Inactive' })).toEqual({ status: 'Inactive' })
    expect(validateSearch({ status: 'Archived' })).toEqual({ status: 'Archived' })
  })

  it('drops a status the list does not offer', () => {
    // Pending/Deleted are real BaseStatus values but absent from this filter,
    // so they must not be forwarded just because they would parse.
    expect(validateSearch({ status: 'Pending' })).toEqual({})
    expect(validateSearch({ status: 'Deleted' })).toEqual({})
  })

  it('drops junk rather than forwarding it as a query param', () => {
    expect(validateSearch({ status: 'active' })).toEqual({}) // case matters
    expect(validateSearch({ status: '' })).toEqual({})
    expect(validateSearch({ status: 42 })).toEqual({})
    expect(validateSearch({ status: null })).toEqual({})
  })

  it('survives a round trip alongside the filters it sits next to', () => {
    expect(
      validateSearch({
        status: 'Active',
        type: 'ClientEmployee',
        client_id: 'c1',
        search: 'ada',
      }),
    ).toEqual({
      status: 'Active',
      type: 'ClientEmployee',
      client_id: 'c1',
      search: 'ada',
    })
  })

  it('is absent when unset, so no status param is sent at all', () => {
    expect(validateSearch({})).toEqual({})
    expect('status' in validateSearch({})).toBe(false)
  })
})
