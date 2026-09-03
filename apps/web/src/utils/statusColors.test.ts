import { describe, expect, it } from 'vitest'

import { getStatusColors } from '@/utils/statusColors'

describe('getStatusColors', () => {
  it('never pairs bg-muted with text-white (that combination renders at ~1.09:1 contrast)', () => {
    const statuses = [
      'Closed',
      'ReferredOut',
      'Intake',
      'Inactive',
      'Cancelled',
      'Suspended',
      'NoShowClosed',
      'SomeUnmappedFutureStatus',
    ]
    for (const status of statuses) {
      const colors = getStatusColors(status)
      if (colors.bg === 'bg-muted') {
        expect(colors.text).not.toBe('text-white')
      }
    }
  })

  it('Closed uses dark text on its light muted background', () => {
    expect(getStatusColors('Closed')).toEqual({
      bg: 'bg-muted',
      text: 'text-safe-dark',
      border: 'border-safe-dark',
    })
  })

  it('unmapped statuses (the default bucket) use dark text, not white-on-white', () => {
    const colors = getStatusColors('ReferredOut')
    expect(colors.bg).toBe('bg-muted')
    expect(colors.text).toBe('text-safe-dark')
  })
})
