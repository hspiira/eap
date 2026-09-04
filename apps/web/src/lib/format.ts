/**
 * Formatting helpers: single source of truth for dates, times, and money.
 * Prefer these over inlining `new Date(x).toLocaleDateString()` or currency
 * string templates in components, so display drift between routes is eliminated.
 */

const EMPTY = "-"

/** Locale short date, e.g. "7/14/2026". Returns a placeholder for nullish or invalid input. */
export function formatDate(value: string | number | Date | null | undefined): string {
  if (value == null || value === "") return EMPTY
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? EMPTY : d.toLocaleDateString()
}

/** Locale date + time. Returns a placeholder for nullish or invalid input. */
export function formatDateTime(value: string | number | Date | null | undefined): string {
  if (value == null || value === "") return EMPTY
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? EMPTY : d.toLocaleString()
}

/**
 * Currency amount with an optional currency code prefix, e.g. "USD 1,200".
 * Returns a placeholder when the amount is nullish.
 */
export function formatMoney(amount: number | null | undefined, currency?: string | null): string {
  if (amount == null) return EMPTY
  return `${currency ?? ""} ${amount.toLocaleString()}`.trim()
}

/**
 * Convert an ISO datetime string to the value shape a `<input type="datetime-local">`
 * expects (`YYYY-MM-DDTHH:mm`, local time). Returns '' for nullish/invalid input.
 */
export function toLocalDatetimeInput(value: string | null | undefined): string {
  if (!value) return ""
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ""
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/

/**
 * Local calendar day as YYYY-MM-DD, for comparing a date against today.
 *
 * A date-only string is already a calendar day and is returned as given.
 * Parsing it through Date would read it as UTC midnight and land on the
 * previous day for anyone west of UTC.
 */
export function toLocalDateKey(value: string | number | Date): string {
  if (typeof value === "string" && DATE_ONLY.test(value.trim())) return value.trim()
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ""
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

const DAY_PREFIX = /^(\d{4})-(\d{2})-(\d{2})/

function dayUtcMs(key: string): number {
  const [y, m, d] = key.split("-").map(Number)
  return Date.UTC(y, m - 1, d)
}

/**
 * Calendar day a wire value denotes, as YYYY-MM-DD, with no timezone
 * conversion. Contract term bounds are days sent as a UTC-midnight instant, so
 * parsing them to a local Date moves them back a day west of UTC.
 */
export function toDayKey(value: string | null | undefined): string {
  if (!value) return ""
  const m = DAY_PREFIX.exec(value.trim())
  return m ? `${m[1]}-${m[2]}-${m[3]}` : ""
}

/** Locale date for a calendar day held on the wire. */
export function formatDay(value: string | null | undefined): string {
  const key = toDayKey(value)
  if (!key) return EMPTY
  const [y, m, d] = key.split("-").map(Number)
  return new Date(y, m - 1, d).toLocaleDateString()
}

/** Whole days from one calendar day to another. Null if either cannot be read. */
export function daysBetweenDays(
  from: string | null | undefined,
  to: string | null | undefined,
): number | null {
  const a = toDayKey(from)
  const b = toDayKey(to)
  if (!a || !b) return null
  return Math.round((dayUtcMs(b) - dayUtcMs(a)) / 86_400_000)
}

/** Today as a calendar day, for comparing against a wire day. */
export function todayDayKey(): string {
  return toLocalDateKey(new Date())
}

/** Shift a calendar day by whole years, keeping it a day. */
export function addYearsToDay(value: string | null | undefined, years: number): string {
  const key = toDayKey(value)
  if (!key) return ""
  const [y, m, d] = key.split("-").map(Number)
  return new Date(Date.UTC(y + years, m - 1, d)).toISOString().slice(0, 10)
}
