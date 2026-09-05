import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { DatePicker } from "@/components/common/DatePicker"

describe("DatePicker", () => {
  it("renders an existing date and clears an optional value", async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(<DatePicker value="2026-01-15" onChange={onChange} aria-label="Coverage starts" />)

    expect(screen.getByRole("combobox", { name: "Coverage starts" })).toHaveTextContent("2026")
    await user.click(screen.getByRole("combobox", { name: "Coverage starts" }))
    await user.click(screen.getByRole("button", { name: "Clear date" }))

    expect(onChange).toHaveBeenCalledWith("")
  })
})
