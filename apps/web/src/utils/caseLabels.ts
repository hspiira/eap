/**
 * Display labels for case/clinical-note enums. Centralised so the list,
 * detail, and form sheet render identical copy.
 */

import {
  CaseClosureReason,
  CaseReferralSource,
  ClinicalNoteType,
  PresentingProblem,
} from "@/types/enums"

export const CaseReferralSourceLabel: Record<CaseReferralSource, string> = {
  [CaseReferralSource.SELF]: "Self-referred",
  [CaseReferralSource.INFORMAL_MANAGER]: "Informal — manager",
  [CaseReferralSource.FORMAL_MANDATORY]: "Formal — mandatory",
  [CaseReferralSource.HR]: "HR",
  [CaseReferralSource.CISM_FOLLOW_UP]: "CISM follow-up",
  [CaseReferralSource.EMPLOYER_PROACTIVE]: "Employer proactive outreach",
}

export const CasePresentingProblemLabel: Record<PresentingProblem, string> = {
  [PresentingProblem.MENTAL_HEALTH]: "Mental health",
  [PresentingProblem.STRESS]: "Stress",
  [PresentingProblem.RELATIONSHIP]: "Relationship",
  [PresentingProblem.WORK]: "Work",
  [PresentingProblem.FINANCIAL]: "Financial",
  [PresentingProblem.SUBSTANCE]: "Substance use",
  [PresentingProblem.BEREAVEMENT]: "Bereavement",
  [PresentingProblem.TRAUMA]: "Trauma",
  [PresentingProblem.FAMILY_CHILD]: "Family / child",
  [PresentingProblem.OTHER]: "Other",
}

export const CaseClosureReasonLabel: Record<CaseClosureReason, string> = {
  [CaseClosureReason.GOALS_MET]: "Goals met",
  [CaseClosureReason.CLIENT_DISCONTINUED]: "Client discontinued",
  [CaseClosureReason.REFERRED_OUT]: "Referred out",
  [CaseClosureReason.NO_SHOW]: "No-show",
  [CaseClosureReason.SESSION_CAP_REACHED]: "Session cap reached",
  [CaseClosureReason.INELIGIBLE]: "Ineligible",
  [CaseClosureReason.OTHER]: "Other",
}

export const ClinicalNoteTypeLabel: Record<ClinicalNoteType, string> = {
  [ClinicalNoteType.DAP]: "DAP",
  [ClinicalNoteType.SOAP]: "SOAP",
  [ClinicalNoteType.PHONE_CONTACT]: "Phone contact",
  [ClinicalNoteType.CRISIS_CONTACT]: "Crisis contact",
  [ClinicalNoteType.CLOSURE_SUMMARY]: "Closure summary",
  [ClinicalNoteType.SUPERVISION]: "Supervision",
}
