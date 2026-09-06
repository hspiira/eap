import { useState } from "react"

import { fireEvent, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { diagnosesApi } from "@/api/endpoints/diagnoses"
import { DiagnosisSelector } from "@/components/common/DiagnosisSelector"
import { renderWithProviders } from "@/test/utils"

function ControlledHarness({ onChangeSpy }: { onChangeSpy: (id: string | null) => void }) {
  const [value, setValue] = useState<string | null>(null)
  return (
    <DiagnosisSelector
      value={value}
      onChange={(id) => {
        setValue(id)
        onChangeSpy(id)
      }}
    />
  )
}

describe("DiagnosisSelector", () => {
  it("shows placeholder when nothing selected", () => {
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    expect(screen.getByText("Select diagnosis")).toBeInTheDocument()
  })

  it("opens the panel and renders type group headers", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole("button", { name: /select diagnosis/i }))
    await screen.findByPlaceholderText(/search by code or name/i)
    await waitFor(() =>
      expect(screen.getByText(/Mood \(affective\) disorders/i)).toBeInTheDocument(),
    )
  })

  it("expanding a type group reveals its diagnoses", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole("button", { name: /select diagnosis/i }))
    await screen.findByText(/Mood \(affective\) disorders/i)
    await user.click(screen.getByRole("button", { name: /Mood \(affective\) disorders/i }))
    await waitFor(() =>
      expect(screen.getAllByText(/Depressive episode/i).length).toBeGreaterThan(0),
    )
  })

  it("search shows matching diagnoses across types", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole("button", { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search by code or name/i)
    await user.type(input, "post")
    await waitFor(
      () =>
        expect(screen.getAllByText(/Post-traumatic stress disorder/i).length).toBeGreaterThan(0),
      { timeout: 2000 },
    )
  })

  it("selecting a diagnosis fires onChange with its id and closes the panel", async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={onChange} />)

    await user.click(screen.getByRole("button", { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search by code or name/i)
    await user.type(input, "F32.1")
    await waitFor(
      () => expect(screen.getAllByText(/Moderate depressive episode/i).length).toBeGreaterThan(0),
      { timeout: 2000 },
    )
    const matches = screen.getAllByText(/Moderate depressive episode/i)
    const button = matches[0].closest("button")
    if (button) fireEvent.click(button)

    await waitFor(() => expect(onChange).toHaveBeenCalledWith("dx-f32-1"))
  })

  it("shows empty-state when no matches", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole("button", { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search by code or name/i)
    await user.type(input, "zzz-no-match")
    expect(await screen.findByText(/no matches/i)).toBeInTheDocument()
  })

  it("displays selected diagnosis code and name on the trigger", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole("button", { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search by code or name/i)
    await user.type(input, "F32.1")
    await waitFor(
      () => expect(screen.getAllByText(/Moderate depressive episode/i).length).toBeGreaterThan(0),
      { timeout: 2000 },
    )
    const matches = screen.getAllByText(/Moderate depressive episode/i)
    const button = matches[0].closest("button")
    if (button) fireEvent.click(button)

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /F32\.1.*Moderate depressive episode/i }),
      ).toBeInTheDocument(),
    )
  })

  it("renders the tree exactly as the server returns it, overlay included", async () => {
    // The tenant overlay (hide, relabel, reorder) is applied server-side in
    // GET /diagnoses/tree. This pins that the selector has no second opinion:
    // a relabelled row shows its local label and a hidden row is simply absent,
    // because the selector reads that response and nothing else.
    const user = userEvent.setup()
    const getTree = vi.spyOn(diagnosesApi, "getTree").mockResolvedValue({
      types: [
        {
          id: "type-1",
          code: "GBV",
          name: "Relationship Abuse",
          description: null,
          sort_order: 0,
          diagnoses: [
            {
              id: "dx-1",
              code: "DV",
              name: "Domestic Violence",
              type_id: "type-1",
              sort_order: 0,
            },
          ],
        },
      ],
    })

    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole("button", { name: /select diagnosis/i }))

    expect(await screen.findByText("Relationship Abuse")).toBeInTheDocument()
    // A type the overlay hid never reaches the client at all.
    expect(screen.queryByText(/Mood \(affective\) disorders/i)).not.toBeInTheDocument()
    getTree.mockRestore()
  })
})
