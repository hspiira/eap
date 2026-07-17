/**
 * Fixture mode — whether endpoints that have local fixtures should serve them
 * instead of calling the API.
 *
 * This used to be `import.meta.env.DEV`, duplicated in seven endpoint modules.
 * That meant the whole of development silently ran on fabricated data for those
 * resources, with nothing on screen to say so — easy to mistake fixture rows for
 * real ones, and easy to miss that a BE endpoint was broken.
 *
 * The flag is now explicit and overridable. The default is still DEV, so this
 * change is behaviour-preserving: set `VITE_USE_FIXTURES=false` to develop
 * against the real API, or `true` to force fixtures anywhere. When it is on,
 * `FixtureBanner` says so.
 *
 * Longer term these should move to MSW so the app under test makes real
 * requests; this at least makes the seam visible and controllable.
 */
export function useFixtures(): boolean {
  // No import.meta under plain Node (unit tests import endpoints directly).
  if (typeof import.meta === 'undefined') return true

  const flag = import.meta.env.VITE_USE_FIXTURES
  if (flag === 'true') return true
  if (flag === 'false') return false
  return import.meta.env.DEV
}
