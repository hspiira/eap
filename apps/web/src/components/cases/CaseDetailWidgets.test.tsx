import { describe, expect, it } from "vitest"

import { noteBodyEntries } from "@/components/cases/CaseDetailWidgets"

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
