/**
 * The frontend against the error bodies the API actually emits.
 *
 * Bodies here were captured from the running API, not written from the schema:
 * GET /activities/{id} for a missing row, and POST /clients/{id}/activate and
 * /restore for a client already in the target state. The backend moved several
 * of these from 400 to 404/409, so this pins the pairing between the status the
 * API returns and the branch the UI takes.
 */
import { describe, expect, it } from "vitest"

import { parseError } from "@/api/errors"
import { isConflict, isNotFound, normalizeErrorMessage } from "@/lib/errors"

function res(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  })
}

describe("backend error bodies as actually emitted", () => {
  it("404 NOT_FOUND from the ConflictError/NotFoundError handler", async () => {
    const err = await parseError(
      res(404, {
        error: "NOT_FOUND",
        message: "Activity not found",
        details: [],
        timestamp: "2026-09-05T00:00:00Z",
        request_id: "r1",
        path: "/activities/x",
      }),
    )
    expect(isNotFound(err)).toBe(true)
    expect(normalizeErrorMessage(err, "fallback")).toBe("Activity not found")
  })

  it("409 CONFLICT from an already-in-state transition", async () => {
    const err = await parseError(
      res(409, {
        error: "CONFLICT",
        message: "Client is already active",
        details: [],
        timestamp: "2026-09-05T00:00:00Z",
        request_id: "r2",
        path: "/clients/x/activate",
      }),
    )
    expect(isConflict(err)).toBe(true)
    expect(normalizeErrorMessage(err, "fallback")).toBe("Client is already active")
  })

  it("422 VALIDATION_ERROR keeps field details", async () => {
    const err = await parseError(
      res(422, {
        error: "VALIDATION_ERROR",
        message: "Validation failed for 1 field: license_info",
        details: [{ field: "license_info", message: "Field required", code: "missing" }],
        timestamp: "2026-09-05T00:00:00Z",
        request_id: "r3",
        path: "/persons/x/secondary-role",
      }),
    )
    expect(err.status).toBe(422)
    expect(err.fieldErrors).toBeTruthy()
  })
})
