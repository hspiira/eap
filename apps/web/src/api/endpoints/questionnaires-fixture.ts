/**
 * Questionnaire fixture — Joseph 7-variable triage + WOS-5 (post) + PHQ-9 item-9 crisis screen.
 *
 * Replaced by BE `/v1/questionnaires` when Phase 3 BE #2 lands. Locked instruments
 * cannot be edited from the UI; the BE owns the canonical scoring rules.
 */

import type { Questionnaire } from '@/types/entities'
import {
  QuestionnaireAdministration,
  QuestionnaireQuestionType,
} from '@/types/enums'

/** Crisis-rule key — must match `QuestionnaireQuestion.key` for PHQ-9 item-9. */
export const PHQ9_ITEM9_KEY = 'phq9_item9'

const JOSEPH_7VAR: Questionnaire = {
  id: 'qn-joseph-7var',
  code: 'joseph-7var-v1',
  title: 'Joseph 7-Variable Triage',
  description:
    'Pre-call screen capturing the seven outcome variables; emits a PHQ-9 item-9 crisis flag when item is non-zero.',
  administration: QuestionnaireAdministration.PRE,
  is_locked: true,
  questions: [
    {
      id: 'q-jv-1',
      key: 'mood_baseline',
      prompt: 'How would you describe your overall mood in the past two weeks?',
      type: QuestionnaireQuestionType.SCALE,
      required: true,
      scale_min: 0,
      scale_max: 10,
      scale_min_label: 'Very low',
      scale_max_label: 'Very good',
    },
    {
      id: 'q-jv-2',
      key: 'sleep_quality',
      prompt: 'On average, how is your sleep quality?',
      type: QuestionnaireQuestionType.SCALE,
      required: true,
      scale_min: 0,
      scale_max: 10,
      scale_min_label: 'Very poor',
      scale_max_label: 'Excellent',
    },
    {
      id: 'q-jv-3',
      key: 'appetite_change',
      prompt: 'Has your appetite changed?',
      type: QuestionnaireQuestionType.SINGLE_CHOICE,
      required: true,
      options: [
        { value: 'increased', label: 'Increased', score: 1 },
        { value: 'unchanged', label: 'Unchanged', score: 0 },
        { value: 'decreased', label: 'Decreased', score: 1 },
      ],
    },
    {
      id: 'q-jv-4',
      key: 'concentration',
      prompt: 'Difficulty concentrating on tasks?',
      type: QuestionnaireQuestionType.SCALE,
      required: true,
      scale_min: 0,
      scale_max: 4,
      scale_min_label: 'Not at all',
      scale_max_label: 'Nearly all the time',
    },
    {
      id: 'q-jv-5',
      key: 'social_withdrawal',
      prompt: 'Have you withdrawn from friends, family, or coworkers?',
      type: QuestionnaireQuestionType.YES_NO,
      required: true,
      options: [
        { value: 'yes', label: 'Yes', score: 1 },
        { value: 'no', label: 'No', score: 0 },
      ],
    },
    {
      id: 'q-jv-6',
      key: 'work_function',
      prompt: 'How is the issue affecting your ability to do your job?',
      type: QuestionnaireQuestionType.SCALE,
      required: true,
      scale_min: 0,
      scale_max: 4,
      scale_min_label: 'No impact',
      scale_max_label: 'Severe impact',
    },
    {
      id: 'q-jv-7',
      key: PHQ9_ITEM9_KEY,
      prompt:
        'In the past two weeks, how often have you been bothered by thoughts that you would be better off dead, or of hurting yourself?',
      type: QuestionnaireQuestionType.SCALE,
      required: true,
      scale_min: 0,
      scale_max: 3,
      scale_min_label: 'Not at all',
      scale_max_label: 'Nearly every day',
      help_text:
        'PHQ-9 item 9. Any non-zero answer triggers an inline crisis alert and the crisis-protocol checklist.',
    },
  ],
}

const WOS5_POST: Questionnaire = {
  id: 'qn-wos5-post',
  code: 'wos5-post-v1',
  title: 'WOS-5 — Post-call Wellbeing',
  description:
    'WHO-5 / WOS-5 wellbeing index administered after the call. Outcomes report computes the pre/post delta.',
  administration: QuestionnaireAdministration.POST,
  is_locked: true,
  questions: [
    {
      id: 'q-w5-1',
      key: 'wos5_cheerful',
      prompt: 'I have felt cheerful and in good spirits.',
      type: QuestionnaireQuestionType.SCALE,
      required: true,
      scale_min: 0,
      scale_max: 5,
      scale_min_label: 'At no time',
      scale_max_label: 'All of the time',
    },
    {
      id: 'q-w5-2',
      key: 'wos5_calm',
      prompt: 'I have felt calm and relaxed.',
      type: QuestionnaireQuestionType.SCALE,
      required: true,
      scale_min: 0,
      scale_max: 5,
      scale_min_label: 'At no time',
      scale_max_label: 'All of the time',
    },
    {
      id: 'q-w5-3',
      key: 'wos5_active',
      prompt: 'I have felt active and vigorous.',
      type: QuestionnaireQuestionType.SCALE,
      required: true,
      scale_min: 0,
      scale_max: 5,
      scale_min_label: 'At no time',
      scale_max_label: 'All of the time',
    },
    {
      id: 'q-w5-4',
      key: 'wos5_rested',
      prompt: 'I woke up feeling fresh and rested.',
      type: QuestionnaireQuestionType.SCALE,
      required: true,
      scale_min: 0,
      scale_max: 5,
      scale_min_label: 'At no time',
      scale_max_label: 'All of the time',
    },
    {
      id: 'q-w5-5',
      key: 'wos5_interest',
      prompt: 'My daily life has been filled with things that interest me.',
      type: QuestionnaireQuestionType.SCALE,
      required: true,
      scale_min: 0,
      scale_max: 5,
      scale_min_label: 'At no time',
      scale_max_label: 'All of the time',
    },
  ],
}

const QUESTIONNAIRE_STORE: Questionnaire[] = [JOSEPH_7VAR, WOS5_POST]

export function fixtureGetAllQuestionnaires(): Questionnaire[] {
  return QUESTIONNAIRE_STORE
}

export function fixtureGetQuestionnaireByCode(code: string): Questionnaire | undefined {
  return QUESTIONNAIRE_STORE.find((q) => q.code === code)
}

/**
 * Crisis-rule evaluator. Currently only PHQ-9 item-9 > 0 — the SAD §11 protocol target.
 * Returns the human-readable list of reasons; empty array means no crisis flag.
 */
export function evaluateCrisisRules(
  answers: Record<string, string | number | string[] | null>,
): string[] {
  const reasons: string[] = []
  const phq9 = answers[PHQ9_ITEM9_KEY]
  if (typeof phq9 === 'number' && phq9 > 0) {
    reasons.push('PHQ-9 item 9 > 0 — self-harm screen positive')
  }
  return reasons
}
