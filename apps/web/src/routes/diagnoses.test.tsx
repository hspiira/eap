import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/api/endpoints/diagnoses", () => ({
  diagnosesApi: {
    getTree: vi.fn(),
    capabilities: vi.fn(),
    listOverlay: vi.fn(),
    setOverlay: vi.fn(),
    listAliases: vi.fn(),
    upsertAlias: vi.fn(),
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
  vi.mocked(diagnosesApi.listAliases).mockResolvedValue([])
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

    await screen.findAllByText("Gender-Based Violence")
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

    await screen.findAllByText("Gender-Based Violence")
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

    await screen.findAllByText("Gender-Based Violence")
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
    await screen.findAllByText("Addictions")
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
    await screen.findAllByText("Addictions")

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
    await screen.findAllByText("Addictions")

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
    await screen.findAllByText("Addictions")
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

    await screen.findAllByText("Relationship Abuse")
    expect(screen.getByText(/renamed from Gender-Based Violence/i)).toBeInTheDocument()
  })

  it("shows the alias review queue to a platform admin", async () => {
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(TREE)
    vi.mocked(diagnosesApi.capabilities).mockResolvedValue({
      can_manage_taxonomy: true,
      can_manage_overlay: false,
    })
    vi.mocked(diagnosesApi.listAliases).mockResolvedValue([
      {
        id: "dxa_inf_0000",
        raw_value: "Personality",
        normalised_key: "personality",
        diagnosis_type_id: "t_gbv",
        diagnosis_id: null,
        source: "inferred_review_2026_09",
        confidence: "inferred",
      },
    ])

    renderPage()

    expect(await screen.findByText(/awaiting review/i)).toBeInTheDocument()
    expect(screen.getByText("Personality")).toBeInTheDocument()
  })

  it("does not fetch aliases for a caller who cannot manage the taxonomy", async () => {
    // The alias list is platform-gated; asking would only earn a 403.
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(TREE)
    vi.mocked(diagnosesApi.capabilities).mockResolvedValue({
      can_manage_taxonomy: false,
      can_manage_overlay: true,
    })
    vi.mocked(diagnosesApi.listOverlay).mockResolvedValue([])

    renderPage()

    await screen.findAllByText("Gender-Based Violence")
    expect(diagnosesApi.listAliases).not.toHaveBeenCalled()
  })
})

describe("descriptions", () => {
  /**
   * The taxonomy carries a clinical definition on every row. Before this it was
   * writable in the form sheet and readable through the API but rendered
   * nowhere, so a curator could only see it by opening the edit form.
   */
  const DESCRIBED = {
    types: [
      {
        id: "t_gbv",
        code: "GBV",
        name: "Gender-Based Violence",
        description: "Violence directed at a person on the basis of gender.",
        sort_order: 0,
        diagnoses: [
          {
            id: "d_dv",
            code: "DV",
            name: "Domestic Violence",
            description: "Physical, sexual or psychological violence by a partner.",
            type_id: "t_gbv",
            sort_order: 0,
          },
        ],
      },
    ],
  }

  beforeEach(() => {
    vi.mocked(diagnosesApi.capabilities).mockResolvedValue({
      can_manage_taxonomy: true,
      can_manage_overlay: true,
    })
    vi.mocked(diagnosesApi.listOverlay).mockResolvedValue([])
  })

  it("shows a type's description on its row", async () => {
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(DESCRIBED)

    renderPage()

    expect(
      await screen.findByText("Violence directed at a person on the basis of gender."),
    ).toBeInTheDocument()
  })

  it("shows a diagnosis description under the selected type", async () => {
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(DESCRIBED)
    renderPage()

    // The first type is selected on arrival, so its diagnoses are already there.
    expect(
      await screen.findByText("Physical, sexual or psychological violence by a partner."),
    ).toBeInTheDocument()
  })

  it("follows a click to another type's diagnoses", async () => {
    vi.mocked(diagnosesApi.getTree).mockResolvedValue({
      types: [
        DESCRIBED.types[0],
        {
          id: "t_str",
          code: "STR",
          name: "Stress",
          description: "Pressure that outruns coping.",
          sort_order: 1,
          diagnoses: [
            {
              id: "d_burn",
              code: "BRN",
              name: "Burnout",
              description: "Exhaustion from prolonged workplace stress.",
              type_id: "t_str",
              sort_order: 0,
            },
          ],
        },
      ],
    })
    const user = userEvent.setup()
    renderPage()
    await screen.findAllByText("Gender-Based Violence")
    expect(
      screen.queryByText("Exhaustion from prolonged workplace stress."),
    ).not.toBeInTheDocument()

    await user.click(screen.getByRole("cell", { name: /^Stress$/ }))

    expect(
      await screen.findByText("Exhaustion from prolonged workplace stress."),
    ).toBeInTheDocument()
    expect(
      screen.queryByText("Physical, sexual or psychological violence by a partner."),
    ).not.toBeInTheDocument()
  })

  it("renders no placeholder when a row has no description", async () => {
    vi.mocked(diagnosesApi.getTree).mockResolvedValue(TREE)

    renderPage()

    await screen.findAllByText("Gender-Based Violence")
    expect(screen.queryByText(/^null$/)).not.toBeInTheDocument()
    expect(screen.queryByText(/undefined/)).not.toBeInTheDocument()
  })
})
