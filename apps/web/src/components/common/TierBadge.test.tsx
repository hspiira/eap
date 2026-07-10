import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TierBadge } from '@/components/common/TierBadge'
import { ClientTier } from '@/types/enums'

describe('TierBadge', () => {
  it('renders Tier A label', () => {
    render(<TierBadge tier={ClientTier.A} />)
    expect(screen.getByText('Tier A')).toBeInTheDocument()
  })

  it('renders Tier B label', () => {
    render(<TierBadge tier={ClientTier.B} />)
    expect(screen.getByText('Tier B')).toBeInTheDocument()
  })

  it('renders Tier C label', () => {
    render(<TierBadge tier={ClientTier.C} />)
    expect(screen.getByText('Tier C')).toBeInTheDocument()
  })

  it('renders an em-dash placeholder when tier is null', () => {
    render(<TierBadge tier={null} />)
    expect(screen.getByLabelText(/tier not set/i)).toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('renders an em-dash placeholder when tier is undefined', () => {
    render(<TierBadge tier={undefined} />)
    expect(screen.getByLabelText(/tier not set/i)).toBeInTheDocument()
  })

  it('uses different visual tone per tier (sanity check)', () => {
    const { rerender } = render(<TierBadge tier={ClientTier.A} />)
    const badgeA = screen.getByLabelText('Tier A')
    const aClasses = badgeA.className

    rerender(<TierBadge tier={ClientTier.C} />)
    const badgeC = screen.getByLabelText('Tier C')
    expect(badgeC.className).not.toBe(aClasses)
  })

  it('forwards className', () => {
    render(<TierBadge tier={ClientTier.A} className="custom-class" />)
    expect(screen.getByLabelText('Tier A').className).toContain('custom-class')
  })
})
