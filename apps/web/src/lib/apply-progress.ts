/** Progress readout for a chunked import apply. */

export interface ApplyPace {
  percent: number
  /** Rows per second so far, or null until there is enough to measure. */
  rate: number | null
  /** Human-readable time left, or null while the rate is still unknown. */
  eta: string | null
}

const MIN_ROWS_TO_ESTIMATE = 5

/** Percentage, measured write rate, and time left for a run in flight. */
export function applyPace(
  done: number,
  total: number,
  startedAt: number,
  now: number,
): ApplyPace {
  const percent = total > 0 ? Math.min(100, Math.round((done / total) * 100)) : 100
  const elapsed = (now - startedAt) / 1000
  if (done < MIN_ROWS_TO_ESTIMATE || elapsed <= 0) return { percent, rate: null, eta: null }
  const rate = done / elapsed
  const left = Math.max(0, total - done)
  if (rate <= 0) return { percent, rate: null, eta: null }
  return { percent, rate, eta: left === 0 ? null : formatEta(left / rate) }
}

function formatEta(seconds: number): string {
  if (seconds < 45) return "under a minute left"
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `about ${minutes} min left`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest === 0 ? `about ${hours} h left` : `about ${hours} h ${rest} min left`
}
