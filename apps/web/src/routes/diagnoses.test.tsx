import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/api/endpoints/diagnoses", () => ({
  diagnosesApi: {
    getTree: vi.fn(),
    capabilities: vi.fn(),
    listOverlay: vi.fn(),
    setOverlay: vi.fn(),
  },
}))

vi.mock("@/components/AppLayout", () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

import { diagnosesApi } from "@/api/endpoints/diagnoses"

import { Route } from "./diagnoses"

const TREE = {
  types: [
    {
      id: "t_gbv",
      code: "GBV",
      name: "Gender-Based Violence",
      description: null,
      sort_order: 0,
      diagnoses: [
        {
          id: "d_dv",
          code: "DV",
          name: "Domestic Violence",
          description: null,
          type_id: "t_gbv",
          sort_order: 0,
        },
      ],
    },
  ],
}

function makeType(id: string, name: string, sortOrder: number) {
  return {
    id,
    code: id.toUpperCase(),
    name,
    description: null,
    sort_order: sortOrder,
    diagnoses: [],
  }
}

/** Three siblings, so a middle row has a neighbour on both sides. */
const THREE_TYPES = {
  types: [
    makeType("t_a", "Addictions", 0),
    makeType("t_b", "Burnout", 1),
    makeType("t_c", "Career", 2),
  ],
}

function renderPage() {
  const Page = Route.options.component as React.ComponentType
  return render(<Page />)
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(diagnosesApi.setOverlay).mockResolvedValue({
    diagnosis_type_id: "t_a",
    diagnosis_id: null,
    is_enabled: true,
    sort_order: 0,
    local_label: null,
  })
})

describe("diagnoses admin page", () => {
  it("hides taxonomy controls from a tenant that cannot manage them", async () => {
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(TREE)
    vi.mocked(diagnosesApi.capabilities).mockResolvedValue({
      can_manage_taxonomy: false,
      can_manage_overlay: true,
    })
    vi.mocked(diagnosesApi.listOverlay).mockResolvedValue([])

    renderPage()

    await waitFor(() => expect(screen.getByText("Gender-Based Violence")).toBeInTheDocument())
    expect(screen.queryByRole("button", { name: /add type/i })).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/edit shared row/i)).not.toBeInTheDocument()
  })

  it("shows taxonomy controls to a platform admin", async () => {
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(TREE)
    vi.mocked(diagnosesApi.capabilities).mockResolvedValue({
      can_manage_taxonomy: true,
      can_manage_overlay: false,
    })

    renderPage()

    await waitFor(() => expect(screen.getByText("Gender-Based Violence")).toBeInTheDocument())
    expect(screen.getByRole("button", { name: /add type/i })).toBeInTheDocument()
  })

  it("does not fetch the overlay when the caller cannot manage it", async () => {
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(TREE)
    vi.mocked(diagnosesApi.capabilities).mockResolvedValue({
      can_manage_taxonomy: true,
      can_manage_overlay: false,
    })
    vi.mocked(diagnosesApi.listOverlay).mockClear()

    renderPage()

    await waitFor(() => expect(screen.getByText("Gender-Based Violence")).toBeInTheDocument())
    expect(diagnosesApi.listOverlay).not.toHaveBeenCalled()
  })

  it("reorders a type by writing every sibling's position", async () => {
    // A partial write would leave the moved row tied with siblings that still
    // inherit a null sort_order, and the tie breaks on name.
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(THREE_TYPES)
    vi.mocked(diagnosesApi.capabilities).mockResolvedValue({
      can_manage_taxonomy: false,
      can_manage_overlay: true,
    })
    vi.mocked(diagnosesApi.listOverlay).mockResolvedValue([])
    const user = userEvent.setup()

    renderPage()
    await waitFor(() => expect(screen.getByText("Addictions")).toBeInTheDocument())
    await user.click(screen.getByRole("button", { name: "Move Burnout up" }))

    await waitFor(() => expect(diagnosesApi.setOverlay).toHaveBeenCalledTimes(3))
    const written = vi.mocked(diagnosesApi.setOverlay).mock.calls.map(([c]) => c)
    expect(written).toEqual([
      { diagnosis_type_id: "t_b", diagnosis_id: null, sort_order: 0 },
      { diagnosis_type_id: "t_a", diagnosis_id: null, sort_order: 1 },
      { diagnosis_type_id: "t_c", diagnosis_id: null, sort_order: 2 },
    ])
  })

  it("cannot move the first row up or the last row down", async () => {
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(THREE_TYPES)
    vi.mocked(diagnosesApi.capabilities).mockResolvedValue({
      can_manage_taxonomy: false,
      can_manage_overlay: true,
    })
    vi.mocked(diagnosesApi.listOverlay).mockResolvedValue([])

    renderPage()
    await waitFor(() => expect(screen.getByText("Addictions")).toBeInTheDocument())

    expect(screen.getByRole("button", { name: "Move Addictions up" })).toBeDisabled()
    expect(screen.getByRole("button", { name: "Move Career down" })).toBeDisabled()
    expect(screen.getByRole("button", { name: "Move Addictions down" })).toBeEnabled()
  })

  it("does not offer reordering to a caller who cannot manage the overlay", async () => {
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(THREE_TYPES)
    vi.mocked(diagnosesApi.capabilities).mockResolvedValue({
      can_manage_taxonomy: true,
      can_manage_overlay: false,
    })

    renderPage()
    await waitFor(() => expect(screen.getByText("Addictions")).toBeInTheDocument())

    expect(screen.queryByRole("button", { name: /^Move /i })).not.toBeInTheDocument()
  })

  it("hides reordering while a search is filtering the list", async () => {
    // Positions written from a filtered list would not be the real ones.
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(THREE_TYPES)
    vi.mocked(diagnosesApi.capabilities).mockResolvedValue({
      can_manage_taxonomy: false,
      can_manage_overlay: true,
    })
    vi.mocked(diagnosesApi.listOverlay).mockResolvedValue([])
    const user = userEvent.setup()

    renderPage()
    await waitFor(() => expect(screen.getByText("Addictions")).toBeInTheDocument())
    expect(screen.getByRole("button", { name: "Move Burnout up" })).toBeInTheDocument()

    await user.type(screen.getByPlaceholderText("Search types and diagnoses"), "Burn")

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: /^Move /i })).not.toBeInTheDocument(),
    )
  })

  it("shows a locally renamed row under its local label", async () => {
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(TREE)
    vi.mocked(diagnosesApi.capabilities).mockResolvedValue({
      can_manage_taxonomy: false,
      can_manage_overlay: true,
    })
    vi.mocked(diagnosesApi.listOverlay).mockResolvedValue([
      {
        diagnosis_type_id: "t_gbv",
        diagnosis_id: null,
        is_enabled: true,
        sort_order: null,
        local_label: "Relationship Abuse",
      },
    ])

    renderPage()

    await waitFor(() => expect(screen.getByText("Relationship Abuse")).toBeInTheDocument())
    expect(screen.getByText(/renamed from Gender-Based Violence/i)).toBeInTheDocument()
  })
})
