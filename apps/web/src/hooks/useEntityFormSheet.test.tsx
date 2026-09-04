import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { z } from "zod"

import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { TestProviders } from "@/test/utils"

const schema = z.object({ name: z.string() })
const defaultValues = { name: "" }

function Harness({ open }: { open: boolean }) {
  const { register } = useEntityFormSheet({
    resource: "test",
    schema,
    defaultValues,
    open,
    onOpenChange: vi.fn(),
    parsePayload: (values) => values,
    save: vi.fn().mockResolvedValue({}),
  })

  return <input aria-label="Name" {...register("name")} />
}

function renderHarness(open: boolean) {
  return render(
    <TestProviders>
      <Harness open={open} />
    </TestProviders>,
  )
}

describe("useEntityFormSheet", () => {
  it("preserves an unsaved draft when the sheet is closed and reopened", () => {
    const view = renderHarness(true)
    const input = screen.getByLabelText("Name")
    fireEvent.change(input, { target: { value: "Draft client" } })

    view.rerender(
      <TestProviders>
        <Harness open={false} />
      </TestProviders>,
    )
    view.rerender(
      <TestProviders>
        <Harness open />
      </TestProviders>,
    )

    expect(screen.getByLabelText("Name")).toHaveValue("Draft client")
  })
})
