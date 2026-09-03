/**
 * Whether endpoints with local fixtures should serve them instead of calling the
 * API. Defaults to DEV; set VITE_USE_FIXTURES to override. FixtureBanner shows
 * when it's on.
 */
export function useFixtures(): boolean {
  // No import.meta under plain Node (unit tests import endpoints directly).
  if (typeof import.meta === 'undefined') return true

  const flag = import.meta.env.VITE_USE_FIXTURES
  if (flag === 'true') return true
  if (flag === 'false') return false
  return import.meta.env.DEV
}
