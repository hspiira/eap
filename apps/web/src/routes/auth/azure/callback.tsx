import { useEffect, useState } from 'react'

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { AlertCircle, Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { authActions } from '@/lib/auth-store'

export const Route = createFileRoute('/auth/azure/callback')({
  component: AzureCallbackPage,
  validateSearch: (search: Record<string, unknown>) => ({
    redirect:
      typeof search.redirect === 'string' && search.redirect.startsWith('/')
        ? search.redirect
        : '/',
    error: typeof search.error === 'string' ? search.error : undefined,
  }),
})

type State =
  | { kind: 'loading' }
  | { kind: 'error'; message: string }

function AzureCallbackPage() {
  const navigate = useNavigate()
  const search = Route.useSearch()
  const [state, setState] = useState<State>(() =>
    search.error ? { kind: 'error', message: search.error } : { kind: 'loading' },
  )

  useEffect(() => {
    if (state.kind === 'error') return

    let cancelled = false

    async function hydrate() {
      try {
        if (window.location.hash.startsWith('#access_token=')) {
          await authActions.bootstrapFromHash()
        } else {
          await authActions.bootstrapFromCookies()
        }
        if (!cancelled) {
          navigate({ to: search.redirect, replace: true })
        }
      } catch (err) {
        if (cancelled) return
        const message = err instanceof Error ? err.message : 'Sign-in failed'
        setState({ kind: 'error', message })
      }
    }

    void hydrate()
    return () => {
      cancelled = true
    }
  }, [navigate, search.redirect, state.kind])

  return (
    <div className="bg-surface text-fg p-8 rounded-sm border border-border-strong shadow-lg">
      <div className="text-center mb-6">
        <h1 className="text-3xl font-semibold text-primary mb-2">Evexía</h1>
        <p className="text-fg-muted">
          {state.kind === 'loading' ? 'Completing sign-in…' : 'Sign-in failed'}
        </p>
      </div>

      {state.kind === 'loading' ? (
        <div className="flex flex-col items-center gap-3 py-6" role="status" aria-live="polite">
          <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden="true" />
          <p className="text-sm text-fg-muted">Linking your Microsoft account…</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div
            className="flex gap-3 p-3 bg-danger-soft border border-danger/30 text-danger-fg text-sm rounded-sm"
            role="alert"
          >
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <p className="font-semibold">We couldn't sign you in</p>
              <p className="mt-1">{state.message}</p>
            </div>
          </div>
          <Button asChild className="w-full">
            <Link
              to="/auth/login"
              search={{ tenant_code: undefined, email: undefined, redirect: undefined }}
            >
              Back to sign-in
            </Link>
          </Button>
        </div>
      )}
    </div>
  )
}
