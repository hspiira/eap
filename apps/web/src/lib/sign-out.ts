import { authActions } from "@/lib/auth-store"

/** Where a signed-out user lands. */
export const SIGN_IN_PATH = "/auth/login"

/**
 * Sign out, then leave the app through a full document load.
 *
 * A client navigation would keep the signed-in user's React tree, query cache
 * and module state alive in memory, and would leave every page they had open
 * sitting in history as a live route. Reloading drops all of it. `replace`
 * rather than `assign` spends the authed entry the user is standing on instead
 * of stacking sign-in on top of it.
 */
export async function signOutAndRedirect(): Promise<void> {
  try {
    await authActions.logout()
  } finally {
    // Leave regardless. A teardown that throws half way is the case where
    // staying put is most dangerous, not least: the session may already be
    // revoked server-side while the page still shows the last user's data.
    if (typeof window !== "undefined") window.location.replace(SIGN_IN_PATH)
  }
}
