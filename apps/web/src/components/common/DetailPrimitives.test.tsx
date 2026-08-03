import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { DetailRow } from "@/components/common/DetailPrimitives"

describe("DetailRow", () => {
  it("wraps instead of truncating a fullWidth value", () => {
    const long = "A".repeat(300)
    render(<DetailRow label="Referral notes" value={long} fullWidth />)
    const dd = screen.getByText(long)
    expect(dd.className).not.toContain("truncate")
    expect(dd.className).toContain("whitespace-pre-wrap")
  })

  it("still truncates a non-fullWidth value but exposes the full text via title", () => {
    const long = "B".repeat(300)
    render(<DetailRow label="Closure reason" value={long} />)
    const dd = screen.getByText(long)
    expect(dd.className).toContain("truncate")
    expect(dd).toHaveAttribute("title", long)
  })
})
