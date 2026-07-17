import { describe, expect, it, vi } from 'vitest'

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: () => null,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

const { renewalParams } = await import('@/routes/contracts/index')

const NOW = new Date('2026-07-13T12:00:00.000Z')

/**
 * The renewal window used to be a client-side filter over one fetched page,
 * keyed on `renewal_date ?? end_date` — neither of which the BE sends — so it
 * returned an empty list in every window. It now maps to server params.
 */
describe('renewalParams', () => {
  it('sends nothing when no window is selected', () => {
    expect(renewalParams('all', NOW)).toEqual({})
  })

  describe('"Renews in N days"', () => {
    it('bounds the term end to the window', () => {
      const p = renewalParams('30d', NOW)
      expect(p.ends_from).toBe('2026-07-13T12:00:00.000Z')
      expect(p.ends_to).toBe('2026-08-12T12:00:00.000Z')
    })

    it('only matches contracts that actually renew', () => {
      // A contract ending inside the window without auto-renew is expiring,
      // not renewing — the label would otherwise lie.
      expect(renewalParams('30d', NOW).is_auto_renew).toBe(true)
      expect(renewalParams('90d', NOW).is_auto_renew).toBe(true)
    })

    it('honours the 90-day window', () => {
      expect(renewalParams('90d', NOW).ends_to).toBe('2026-10-11T12:00:00.000Z')
    })

    it('never looks backwards', () => {
      const p = renewalParams('30d', NOW)
      expect(new Date(p.ends_from!).getTime()).toBe(NOW.getTime())
    })
  })

  describe('"Already expired"', () => {
    it('bounds the term end at now, with no lower bound', () => {
      const p = renewalParams('expired', NOW)
      expect(p.ends_to).toBe('2026-07-13T12:00:00.000Z')
      expect(p.ends_from).toBeUndefined()
    })

    it('does not filter on auto-renew — an expired term is expired either way', () => {
      expect(renewalParams('expired', NOW).is_auto_renew).toBeUndefined()
    })
  })

  it('is a pure function of the clock it is given', () => {
    const other = new Date('2030-01-01T00:00:00.000Z')
    expect(renewalParams('30d', NOW)).not.toEqual(renewalParams('30d', other))
    expect(renewalParams('30d', NOW)).toEqual(renewalParams('30d', new Date(NOW)))
  })
})
