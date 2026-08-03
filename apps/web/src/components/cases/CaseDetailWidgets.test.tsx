import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { CloseCaseDialog, noteBodyEntries } from "@/components/cases/CaseDetailWidgets"
import { renderWithProviders } from "@/test/utils"
import { CaseReferralSource, CaseStatus, PresentingProblem } from "@/types/enums"

// jsdom doesn't implement the Pointer Events capture APIs or scrollIntoView that
// Radix's Select relies on, so opening it via userEvent throws without these stubs.
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false
}
if (!Element.prototype.setPointerCapture) {
  Element.prototype.setPointerCapture = () => {}
}
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = () => {}
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {}
}

describe("noteBodyEntries", () => {
  it("labels each populated DAP section instead of concatenating them", () => {
    const entries = noteBodyEntries({
      data: "Client reports poor sleep.",
      assessment: "Consistent with adjustment disorder.",
      plan: "Introduce sleep hygiene techniques.",
    })
    expect(entries).toEqual([
      ["Data", "Client reports poor sleep."],
      ["Assessment", "Consistent with adjustment disorder."],
      ["Plan", "Introduce sleep hygiene techniques."],
    ])
  })

  it("omits empty sections", () => {
    const entries = noteBodyEntries({ data: "", assessment: "Has content", plan: "" })
    expect(entries).toEqual([["Assessment", "Has content"]])
  })

  it("labels SOAP sections", () => {
    const entries = noteBodyEntries({
      subjective: "Reports fatigue.",
      objective: "Alert and oriented.",
      assessment: "",
      plan: "",
    })
    expect(entries).toEqual([
      ["Subjective", "Reports fatigue."],
      ["Objective", "Alert and oriented."],
    ])
  })

  it("labels a narrative summary", () => {
    expect(noteBodyEntries({ summary: "Phone contact, brief check-in." })).toEqual([
      ["Summary", "Phone contact, brief check-in."],
    ])
  })

  it("orders fully-populated SOAP sections correctly (Subjective, Objective, Assessment, Plan)", () => {
    const entries = noteBodyEntries({
      subjective: "Reports fatigue and difficulty concentrating.",
      objective: "BP 120/80, HR 72, alert and oriented x3.",
      assessment: "Adjustment disorder with mixed mood disturbance.",
      plan: "Prescribe sertraline 50mg daily; follow-up in 2 weeks.",
    })
    expect(entries).toEqual([
      ["Subjective", "Reports fatigue and difficulty concentrating."],
      ["Objective", "BP 120/80, HR 72, alert and oriented x3."],
      ["Assessment", "Adjustment disorder with mixed mood disturbance."],
      ["Plan", "Prescribe sertraline 50mg daily; follow-up in 2 weeks."],
    ])
  })
})

function activeCaseWithNoClosureScreener() {
  return {
    id: "case-1",
    tenant_id: "t-1",
    clinical_subject_id: "cs_1",
    client_id: "c-1",
    presenting_problem: PresentingProblem.STRESS,
    referral_source: CaseReferralSource.SELF,
    status: CaseStatus.ACTIVE,
    opened_at: "2026-01-01T00:00:00Z",
    assigned_counsellor_id: "u-1",
    authorization_id: null,
    referred_by_user_id: null,
    referral_notes: null,
    closed_at: null,
    closure_reason: null,
    closure_summary_note_id: null,
    intake_screener_admin_ids: [],
    closure_screener_admin_ids: [],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  }
}

describe("CloseCaseDialog", () => {
  it("always shows why Goals met is disabled, even before it's selected", async () => {
    renderWithProviders(
      <CloseCaseDialog
        open
        onOpenChange={vi.fn()}
        caseData={activeCaseWithNoClosureScreener() as never}
        onConfirm={vi.fn()}
      />,
    )
    expect(
      await screen.findByText(/goals-met closure needs a closure screener recorded first/i),
    ).toBeInTheDocument()
  })

  it("the disabled Goals met option carries an explanatory title attribute", async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <CloseCaseDialog
        open
        onOpenChange={vi.fn()}
        caseData={activeCaseWithNoClosureScreener() as never}
        onConfirm={vi.fn()}
      />,
    )
    await user.click(screen.getByRole("combobox"))
    const goalsMetOption = await screen.findByRole("option", { name: /goals met/i })
    expect(goalsMetOption).toHaveAttribute("title", expect.stringMatching(/closure screener/i))
  })
})
