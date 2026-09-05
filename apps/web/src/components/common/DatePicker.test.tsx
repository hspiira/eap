import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { DatePicker } from "@/components/common/DatePicker"

describe("DatePicker", () => {
  it.each([3, 5, 10, 20, 30])("picks a date %i years ago directly", async (yearsAgo) => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const year = new Date().getFullYear() - yearsAgo
    render(<DatePicker onChange={onChange} aria-label="Date of birth" />)

    await user.click(screen.getByRole("combobox", { name: "Date of birth" }))
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Choose the Year" }),
      String(year),
    )
    await user.selectOptions(screen.getByRole("combobox", { name: "Choose the Month" }), "0")
    await user.click(screen.getByRole("button", { name: new RegExp(`January 15th, ${year}`) }))

    expect(onChange).toHaveBeenCalledExactlyOnceWith(`${year}-01-15`)
    expect(screen.getByRole("combobox", { name: "Date of birth" })).toHaveAttribute(
      "aria-expanded",
      "false",
    )
  })

  it.each(["1880-02-12", "2099-02-12"])("opens at the selected date %s", async (value) => {
    const user = userEvent.setup()
    render(<DatePicker value={value} onChange={vi.fn()} aria-label="Date" />)
    await user.click(screen.getByRole("combobox", { name: "Date" }))
    expect(screen.getByRole("combobox", { name: "Choose the Year" })).toHaveValue(value.slice(0, 4))
    expect(screen.getByRole("combobox", { name: "Choose the Month" })).toHaveValue("1")
  })

  it("allows direct selection of future dates", async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const year = new Date().getFullYear() + 3
    render(<DatePicker onChange={onChange} aria-label="Coverage starts" />)
    await user.click(screen.getByRole("combobox", { name: "Coverage starts" }))
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Choose the Year" }),
      String(year),
    )
    await user.selectOptions(screen.getByRole("combobox", { name: "Choose the Month" }), "0")
    await user.click(screen.getByRole("button", { name: new RegExp(`January 15th, ${year}`) }))
    expect(onChange).toHaveBeenCalledExactlyOnceWith(`${year}-01-15`)
  })

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
