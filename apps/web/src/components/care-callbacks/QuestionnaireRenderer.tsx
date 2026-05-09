/**
 * Dynamic questionnaire renderer for the Phase 3 triage form.
 *
 * Dispatches on `QuestionnaireQuestion.type` and emits a `key → primitive` answers map
 * upstream via `onChange`. Validation lives in the parent form so server-side errors
 * (after BE Phase 3 lands) can be surfaced inline.
 */

import { useId } from "react"

import type { Questionnaire, QuestionnaireQuestion } from "@/types/entities"
import { QuestionnaireQuestionType } from "@/types/enums"

export type AnswerPrimitive = string | number | string[] | null
export type AnswersMap = Record<string, AnswerPrimitive>

interface Props {
  questionnaire: Questionnaire
  answers: AnswersMap
  onChange: (key: string, value: AnswerPrimitive) => void
  /** Read-only mode: render answers but disable inputs. Used on case-detail review. */
  readOnly?: boolean
}

export function QuestionnaireRenderer({ questionnaire, answers, onChange, readOnly }: Props) {
  return (
    <fieldset className="space-y-5">
      <legend className="text-sm font-semibold text-fg">{questionnaire.title}</legend>
      {questionnaire.description ? (
        <p className="text-xs text-fg/60">{questionnaire.description}</p>
      ) : null}
      {questionnaire.questions.map((q) => (
        <QuestionField
          key={q.id}
          question={q}
          value={answers[q.key] ?? null}
          onChange={(v) => onChange(q.key, v)}
          readOnly={readOnly}
        />
      ))}
    </fieldset>
  )
}

interface QuestionFieldProps {
  question: QuestionnaireQuestion
  value: AnswerPrimitive
  onChange: (value: AnswerPrimitive) => void
  readOnly?: boolean
}

function QuestionField({ question, value, onChange, readOnly }: QuestionFieldProps) {
  const labelId = useId()

  return (
    <div className="space-y-1.5">
      <label htmlFor={labelId} className="block text-sm font-medium text-fg">
        {question.prompt}
        {question.required && <span className="ml-1 text-danger-soft">*</span>}
      </label>
      {question.help_text ? (
        <p className="text-xs text-fg/60">{question.help_text}</p>
      ) : null}
      {renderInput(question, value, onChange, readOnly, labelId)}
    </div>
  )
}

function renderInput(
  q: QuestionnaireQuestion,
  value: AnswerPrimitive,
  onChange: (v: AnswerPrimitive) => void,
  readOnly: boolean | undefined,
  inputId: string,
) {
  switch (q.type) {
    case QuestionnaireQuestionType.SCALE:
      return (
        <ScaleInput
          inputId={inputId}
          min={q.scale_min ?? 0}
          max={q.scale_max ?? 10}
          minLabel={q.scale_min_label}
          maxLabel={q.scale_max_label}
          value={typeof value === "number" ? value : null}
          onChange={onChange}
          readOnly={readOnly}
        />
      )
    case QuestionnaireQuestionType.SINGLE_CHOICE:
    case QuestionnaireQuestionType.YES_NO:
      return (
        <select
          id={inputId}
          disabled={readOnly}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value || null)}
          className="flex h-9 w-full rounded-sm border border-fg/20 bg-bg px-3 text-sm text-fg shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
        >
          <option value="">— Select —</option>
          {(q.options ?? []).map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      )
    case QuestionnaireQuestionType.MULTI_CHOICE: {
      const arr = Array.isArray(value) ? value : []
      return (
        <div className="flex flex-wrap gap-2">
          {(q.options ?? []).map((opt) => {
            const checked = arr.includes(opt.value)
            return (
              <label
                key={opt.value}
                className={`inline-flex cursor-pointer items-center gap-1.5 rounded-sm border px-2 py-1 text-sm ${
                  checked
                    ? "border-primary/40 bg-primary/10 text-fg"
                    : "border-fg/20 bg-bg text-fg/75 hover:bg-surface-hover"
                }`}
              >
                <input
                  type="checkbox"
                  disabled={readOnly}
                  checked={checked}
                  onChange={(e) => {
                    const next = e.target.checked
                      ? [...arr, opt.value]
                      : arr.filter((v) => v !== opt.value)
                    onChange(next.length ? next : null)
                  }}
                />
                {opt.label}
              </label>
            )
          })}
        </div>
      )
    }
    case QuestionnaireQuestionType.TEXT:
      return (
        <textarea
          id={inputId}
          rows={3}
          disabled={readOnly}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value || null)}
          className="flex w-full rounded-sm border border-fg/20 bg-bg px-3 py-2 text-sm text-fg shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
        />
      )
  }
}

interface ScaleInputProps {
  inputId: string
  min: number
  max: number
  minLabel?: string | null
  maxLabel?: string | null
  value: number | null
  onChange: (v: number | null) => void
  readOnly?: boolean
}

function ScaleInput({ inputId, min, max, minLabel, maxLabel, value, onChange, readOnly }: ScaleInputProps) {
  const ticks = []
  for (let i = min; i <= max; i++) ticks.push(i)
  return (
    <div className="space-y-1">
      <div className="flex flex-wrap gap-1">
        {ticks.map((t) => {
          const selected = value === t
          return (
            <button
              key={t}
              type="button"
              disabled={readOnly}
              id={t === min ? inputId : undefined}
              aria-pressed={selected}
              onClick={() => onChange(selected ? null : t)}
              className={`min-w-9 rounded-sm border px-2 py-1 text-sm tabular-nums ${
                selected
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-fg/20 bg-bg text-fg hover:bg-surface-hover"
              } ${readOnly ? "cursor-not-allowed opacity-60" : ""}`}
            >
              {t}
            </button>
          )
        })}
      </div>
      <div className="flex justify-between text-xs text-fg/60">
        <span>{minLabel ?? min}</span>
        <span>{maxLabel ?? max}</span>
      </div>
    </div>
  )
}
