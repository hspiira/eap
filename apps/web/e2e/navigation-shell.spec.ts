import { expect, test } from "@playwright/test"

test("navigation preserves the sidebar and exposes the audit console", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem(
      "evexia.auth",
      JSON.stringify({
        token: "synthetic-navigation-token",
        user_id: "user-1",
        email: "admin@example.com",
        token_expires_at: Date.now() + 3_600_000,
      }),
    )
    localStorage.setItem("evexia.tenant", JSON.stringify({ id: "tenant-1" }))
  })
  await page.route("http://localhost:8000/**", async (route) => {
    const path = new URL(route.request().url()).pathname
    const body = path.includes("/tenants/")
      ? { id: "tenant-1", name: "Test tenant", code: "TEST", status: "Active" }
      : path.includes("/users/")
        ? { id: "user-1", email: "admin@example.com", role: "Admin", access_scopes: [] }
        : path.endsWith("/members/stats")
          ? { by_status: {}, with_account: 0, total: 0 }
          : { items: [], total: 0, page: 1, limit: 25, has_more: false }
    await route.fulfill({ json: body })
  })
  await page.goto("/members")
  await page.getByRole("button", { name: "Expand sidebar", exact: true }).click()
  const sidebar = await page.locator('[data-sidebar="sidebar"]').elementHandle()
  const header = await page.getByRole("button", { name: "Account menu" }).elementHandle()
  await page.getByRole("link", { name: "Audits", exact: true }).click()
  await expect(page).toHaveURL(/\/audit$/)
  await expect(page.getByRole("heading", { name: "Audit", exact: true })).toBeVisible()
  expect(await sidebar!.evaluate((element) => element.isConnected)).toBe(true)
  expect(await header!.evaluate((element) => element.isConnected)).toBe(true)
  await expect(page.getByRole("button", { name: "Collapse sidebar" })).toBeVisible()
  await page.getByRole("link", { name: "Members", exact: true }).click()
  await expect(page).toHaveURL(/\/members\/?$/)
  expect(await sidebar!.evaluate((element) => element.isConnected)).toBe(true)
})

for (const theme of ["light", "dark"]) {
  test(`${theme} controls use monochrome tokens and keep pill buttons`, async ({
    page,
  }, testInfo) => {
    await page.addInitScript((mode) => {
      localStorage.setItem("evexia.ui", JSON.stringify({ theme: mode }))
    }, theme)
    await page.goto("/")
    const button = page.getByRole("link", { name: "Sign in to the console", exact: true })
    await expect(button).toBeVisible()
    const style = await button.evaluate((element) => {
      const computed = getComputedStyle(element)
      return { background: computed.backgroundColor, radius: computed.borderRadius }
    })
    expect(style.background).toBe(theme === "dark" ? "rgb(237, 237, 237)" : "rgb(17, 17, 17)")
    expect(parseFloat(style.radius)).toBeGreaterThan(24)
    await button.hover()
    const arrow = button.locator(".lp-sign-in-arrow")
    await expect(arrow).toHaveCSS("animation-name", "lp-arrow-pass")
    await page.emulateMedia({ reducedMotion: "reduce" })
    await expect(arrow).toHaveCSS("animation-name", "none")
    await page.mouse.move(0, 0)
    await page.screenshot({ path: testInfo.outputPath(`landing-${theme}.png`) })
    await button.click()
    const input = page.locator("input:visible").first()
    await input.focus()
    const shadow = await input.evaluate((element) => getComputedStyle(element).boxShadow)
    expect(shadow).toContain(theme === "dark" ? "rgb(237, 237, 237)" : "rgb(17, 17, 17)")
  })
}
