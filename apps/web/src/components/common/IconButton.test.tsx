/**
 * The one icon-only control. Its label is never rendered inline, so the
 * accessible name is the only thing naming the button.
 */

import userEvent from "@testing-library/user-event"
import { Download } from "lucide-react"
import { describe, expect, it, vi } from "vitest"

import { IconButton } from "@/components/common/IconButton"
import { renderWithProviders } from "@/test/utils"

describe("IconButton", () => {
  it("names the button without rendering the label inline", () => {
    const screen = renderWithProviders(<IconButton label="Export" icon={Download} />)
    expect(screen.getByRole("button", { name: "Export" })).toBeInTheDocument()
    expect(screen.queryByText("Export")).not.toBeInTheDocument()
  })

  it("runs its action", async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()
    const screen = renderWithProviders(
      <IconButton label="Export" icon={Download} onClick={onClick} />,
    )
    await user.click(screen.getByRole("button", { name: "Export" }))
    expect(onClick).toHaveBeenCalledOnce()
  })

  it("stays named when disabled, so a row's controls do not shift", () => {
    const screen = renderWithProviders(<IconButton label="Export" icon={Download} disabled />)
    expect(screen.getByRole("button", { name: "Export" })).toBeDisabled()
  })
})
