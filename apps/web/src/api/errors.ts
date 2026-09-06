/**
 * Response body -> ApiError normalization. Pure functions: no client state.
 */

import type { ErrorDetail, FieldErrors } from "@/types/api"
import { ApiError } from "@/types/api"

export async function parseError(response: Response): Promise<ApiError> {
  let body: unknown
  try {
    body = await response.json()
  } catch (_err) {
    body = null
  }

  const message = normalizeErrorMessageBody(body, response)
  const errorCode = normalizeErrorCodeBody(body, response.status)
  const details = normalizeErrorDetailsBody(body)
  const fieldErrors = collapseFieldErrors(details)
  const data = normalizeErrorDataBody(body)

  return new ApiError(message, errorCode, response.status, fieldErrors, data, details)
}

/**
 * Pass through server-provided extra fields (e.g. `retry_after_seconds` for lockout)
 * minus the ones we already extract into typed fields.
 */
function normalizeErrorDataBody(body: unknown): Record<string, unknown> | undefined {
  if (!body || typeof body !== "object") return undefined
  const b = body as Record<string, unknown>
  const reserved = new Set([
    "error",
    "message",
    "detail",
    "details",
    "timestamp",
    "path",
    "request_id",
  ])
  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(b)) {
    if (!reserved.has(k)) out[k] = v
  }
  return Object.keys(out).length > 0 ? out : undefined
}

function normalizeErrorMessageBody(body: unknown, response: Response): string {
  if (body && typeof body === "object") {
    const b = body as Record<string, unknown>
    if (typeof b.message === "string" && b.message) return b.message
    const detail = b.detail
    if (typeof detail === "string" && detail) return detail
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0]
      if (
        first &&
        typeof first === "object" &&
        first !== null &&
        "msg" in first &&
        typeof (first as { msg: unknown }).msg === "string"
      ) {
        return (first as { msg: string }).msg
      }
      return String(first)
    }
  }
  return response.statusText || "An unknown error occurred"
}

function normalizeErrorCodeBody(body: unknown, status: number): string {
  if (body && typeof body === "object") {
    const b = body as Record<string, unknown>
    if (typeof b.error === "string" && b.error) return b.error
  }
  switch (status) {
    case 401:
      return "AUTHENTICATION_ERROR"
    case 403:
      return "AUTHORIZATION_ERROR"
    case 404:
      return "NOT_FOUND"
    default:
      return "HTTP_ERROR"
  }
}

function readString(source: Record<string, unknown>, key: string): string | null {
  const value = source[key]
  return typeof value === "string" && value ? value : null
}

/** The server's `details` array, kept whole so repeated fields are not lost. */
function normalizeErrorDetailsBody(body: unknown): ErrorDetail[] | undefined {
  if (!body || typeof body !== "object") return undefined
  const details = (body as Record<string, unknown>).details
  if (!Array.isArray(details)) return undefined
  const out: ErrorDetail[] = []
  for (const entry of details) {
    if (!entry || typeof entry !== "object") continue
    const d = entry as Record<string, unknown>
    const message = readString(d, "message")
    const field = readString(d, "field")
    if (!message && !field) continue
    out.push({ field, message: message ?? String(entry), code: readString(d, "code") })
  }
  return out.length > 0 ? out : undefined
}

/** One message per field, for attaching to form inputs. Later entries win. */
function collapseFieldErrors(details: ErrorDetail[] | undefined): FieldErrors | undefined {
  if (!details) return undefined
  const acc: FieldErrors = {}
  for (const detail of details) {
    if (detail.field) acc[detail.field] = detail.message
  }
  return Object.keys(acc).length > 0 ? acc : undefined
}
