import { useCallback, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"

import { useToast } from "@/contexts/ToastContext"
import { normalizeErrorMessage } from "@/lib/errors"

const NAMED_FAILURES = 3

export interface BulkActionOptions {
  /**
   * Applied to one id. There are no bulk endpoints, so this runs once per
   * selected row. `reason` is passed through unchanged when `run` receives
   * one, for actions the API rejects without an audit reason.
   */
  action: (id: string, reason?: string) => Promise<unknown>
  /** Query key prefix to invalidate once the run finishes. */
  invalidateKey: readonly unknown[]
  /** Past participle naming what happened, used in the result message. */
  verb: string
  /** Singular noun for the rows being acted on. */
  noun: string
  /** Resolves a row id to something a person recognises, for naming failures. */
  labelFor?: (id: string) => string
  onDone?: () => void
}

export interface BulkActionState {
  run: (ids: ReadonlySet<string>, reason?: string) => Promise<void>
  running: boolean
}

function plural(count: number, noun: string): string {
  return count === 1 ? noun : `${noun}s`
}

/**
 * Applies a single-item action across a selection and reports the outcome.
 *
 * Rows run in sequence so a large selection cannot flood the API, and a
 * failure does not abandon the rows after it. There is no transaction behind
 * these calls, so a run can half succeed; a partial result names the rows that
 * failed rather than reporting a count that reads as success.
 */
export function useBulkAction({
  action,
  invalidateKey,
  verb,
  noun,
  labelFor,
  onDone,
}: BulkActionOptions): BulkActionState {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [running, setRunning] = useState(false)

  const run = useCallback(
    async (ids: ReadonlySet<string>, reason?: string) => {
      if (ids.size === 0) return
      setRunning(true)

      const failedIds: string[] = []
      let firstError: unknown = null

      for (const id of ids) {
        try {
          await action(id, reason)
        } catch (err) {
          failedIds.push(id)
          if (firstError === null) firstError = err
        }
      }

      const succeeded = ids.size - failedIds.length
      if (succeeded > 0) {
        await queryClient.invalidateQueries({ queryKey: invalidateKey })
      }

      if (failedIds.length === 0) {
        toast.showSuccess(`${succeeded} ${plural(succeeded, noun)} ${verb}`)
      } else if (succeeded === 0) {
        toast.showError(normalizeErrorMessage(firstError, `Could not ${verb} any ${noun}`))
      } else {
        const names = failedIds.slice(0, NAMED_FAILURES).map((id) => labelFor?.(id) ?? id)
        const rest = failedIds.length - names.length
        const listed = rest > 0 ? `${names.join(", ")} and ${rest} more` : names.join(", ")
        toast.showError(
          `${succeeded} ${plural(succeeded, noun)} ${verb}. Could not ${verb} ${listed}.`,
        )
      }

      setRunning(false)
      onDone?.()
    },
    [action, invalidateKey, verb, noun, labelFor, onDone, queryClient, toast],
  )

  return { run, running }
}
