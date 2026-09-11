/**
 * The roster importer's chunked apply, in a real browser.
 *
 * The API is stubbed at the network boundary, so this covers what the
 * component tests cannot: the real dialog mounted in a real page, the request
 * sequence the apply loop actually issues, and the progress it renders between
 * chunks. What each chunk does on the server is covered against PostgreSQL in
 * the API's own integration tests.
 */

import { expect, type Page,test } from "@playwright/test"

const TENANT = "tenant-1"
const BATCH = "batch-1"
const TOTAL_ROWS = 250
const API = "http://localhost:8000"

interface ApplyCall {
  limit: string | null
}

function rosterCsv(rows: number): string {
  const lines = ["company_code,staff_id,name_of_employee"]
  for (let n = 1; n <= rows; n += 1) lines.push(`ACM,HR-${n},Member ${n}`)
  return lines.join("\n")
}

function batchBody(overrides: Record<string, unknown> = {}) {
  return {
    id: BATCH,
    tenant_id: TENANT,
    file_name: "roster.csv",
    file_hash: "sha256:abc",
    row_count: TOTAL_ROWS,
    status: "Staged",
    outcome_counts: { New: TOTAL_ROWS },
    staged_by: "user-1",
    applied_by: null,
    applied_at: null,
    created_at: "2026-09-11T00:00:00Z",
    ...overrides,
  }
}

function rowsBody(count: number) {
  return {
    items: Array.from({ length: count }, (_, i) => ({
      id: `row-${i + 1}`,
      row_number: i + 2,
      client_code: "ACM",
      client_name: "Acme",
      import_source_id: `HR-${i + 1}`,
      staff_number: `${1000 + i}`,
      display_label: `Member ${i + 1}`,
      outcome: "New",
      decision: "import",
    })),
    total: count,
    page: 1,
    limit: 200,
    has_more: false,
  }
}

async function signIn(page: Page) {
  await page.addInitScript(
    ([tenant]) => {
      window.localStorage.setItem(
        "evexia.auth",
        JSON.stringify({
          token: "e2e-token",
          refresh_token: null,
          user_id: "user-1",
          email: "admin@example.com",
          token_expires_at: Date.now() + 60 * 60 * 1000,
          csrf_token: null,
        }),
      )
      window.localStorage.setItem("evexia.tenant", JSON.stringify({ id: tenant }))
    },
    [TENANT],
  )
}

/** Answer every call the members page makes, and record the apply chunks. */
async function stubApi(page: Page, applyCalls: ApplyCall[]) {
  let written = 0

  await page.route(`${API}/**`, async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname
    const json = (body: unknown, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) })

    if (path.endsWith("/members/import") && request.method() === "POST") {
      return json(batchBody(), 201)
    }
    if (path.includes("/members/import/") && path.endsWith("/apply")) {
      applyCalls.push({ limit: url.searchParams.get("limit") })
      const chunk = Math.min(Number(url.searchParams.get("limit") ?? 50), TOTAL_ROWS - written)
      written += chunk
      const remaining = TOTAL_ROWS - written
      return json({
        batch_id: BATCH,
        imported: chunk,
        updated: 0,
        unchanged: 0,
        failed: 0,
        remaining,
        done: remaining === 0,
      })
    }
    if (path.includes("/members/import/") && path.includes("/rows")) {
      return json(rowsBody(TOTAL_ROWS))
    }
    if (path.endsWith("/members/stats")) {
      return json({ by_status: {}, with_account: 0, total: 0 })
    }
    if (path.endsWith("/members")) {
      return json({ items: [], total: 0, page: 1, limit: 25, has_more: false })
    }
    if (path.includes("/tenants/")) {
      return json({ id: TENANT, name: "Acme", code: "ACM", status: "Active" })
    }
    return json({ items: [], total: 0, page: 1, limit: 25, has_more: false })
  })
}

/**
 * Answer the file picker with a roster.
 *
 * Chromium takes the File System Access branch, so the dialog opens a native
 * picker no test can drive. Stubbing the handle keeps the test on the same
 * branch real users are on rather than forcing the plain-input fallback.
 */
async function stubFilePicker(page: Page, csv: string) {
  await page.addInitScript(([contents]) => {
    const file = new File([contents], "roster.csv", { type: "text/csv" })
    ;(window as unknown as { showOpenFilePicker: unknown }).showOpenFilePicker = async () => [
      { kind: "file", name: "roster.csv", getFile: async () => file },
    ]
  }, [csv])
}

async function openImportWith(page: Page, csv: string) {
  await stubFilePicker(page, csv)
  await page.goto("/members")
  await page.getByRole("button", { name: "Import", exact: true }).click()
  await page.getByRole("button", { name: /Choose file/ }).click()
  await expect(page.getByRole("button", { name: /roster\.csv/ })).toBeVisible()
}

test.describe("roster import", () => {
  test("applies a staged roster in chunks and reports progress", async ({ page }) => {
    const applyCalls: ApplyCall[] = []
    await signIn(page)
    await stubApi(page, applyCalls)

    await openImportWith(page, rosterCsv(TOTAL_ROWS))
    await expect(page.getByRole("cell", { name: "Member 1", exact: true })).toBeVisible()

    await page.getByRole("button", { name: /Import \d+ rows/ }).click()
    await expect(page.getByRole("button", { name: "Done" })).toBeVisible({ timeout: 15_000 })

    // 250 rows at 200 a call is two chunks, not five at the old size of 50.
    expect(applyCalls).toHaveLength(2)
    expect(applyCalls.every((call) => call.limit === "200")).toBe(true)
  })

  test("a chunk in flight shows progress and can be cancelled", async ({ page }) => {
    const applyCalls: ApplyCall[] = []
    await signIn(page)
    await stubApi(page, applyCalls)

    // Hold the first chunk open so the progress banner is observable.
    await page.route(`${API}/members/import/*/apply*`, async (route) => {
      applyCalls.push({ limit: new URL(route.request().url()).searchParams.get("limit") })
      await new Promise((resolve) => setTimeout(resolve, 1_500))
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          batch_id: BATCH,
          imported: 200,
          updated: 0,
          unchanged: 0,
          failed: 0,
          remaining: 50,
          done: false,
        }),
      })
    })

    await openImportWith(page, rosterCsv(TOTAL_ROWS))
    await page.getByRole("button", { name: /Import \d+ rows/ }).click()

    const cancel = page.getByRole("button", { name: "Cancel" })
    await expect(cancel).toBeVisible()
    await expect(page.getByText(/0 \/ \d+ · 0%/)).toBeVisible()

    await cancel.click()
    await expect(cancel).toBeHidden({ timeout: 15_000 })
  })

  test("nothing is applied until a roster has been staged", async ({ page }) => {
    const applyCalls: ApplyCall[] = []
    await signIn(page)
    await stubApi(page, applyCalls)

    await page.goto("/members")
    await page.getByRole("button", { name: "Import", exact: true }).click()

    await expect(page.getByRole("button", { name: /Choose file/ })).toBeVisible()
    await expect(page.getByRole("button", { name: /Import \d+ rows/ })).toBeDisabled()
    expect(applyCalls).toHaveLength(0)
  })
})
