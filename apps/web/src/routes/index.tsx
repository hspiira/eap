import { createFileRoute, Link } from '@tanstack/react-router'
import { ArrowUpRight, ShieldCheck } from 'lucide-react'

import { AppLayout } from '@/components/AppLayout'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/slices/authSlice'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="grid min-h-svh w-full place-items-center bg-bg text-fg">
        <p className="text-sm text-fg-muted">Loading…</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LandingPage />
  }

  return <AppLayout>{null}</AppLayout>
}

const EMPTY_AUTH_SEARCH = {
  tenant_code: undefined,
  email: undefined,
  redirect: undefined,
} as const

function LandingPage() {
  return (
    <div className="flex min-h-svh flex-col bg-bg text-fg">
      <header className="border-b border-border-subtle">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <Link
            to="/"
            className="flex items-center gap-2 text-base font-semibold tracking-tight text-fg"
          >
            <span
              className="grid size-6 place-items-center rounded-sm bg-primary text-primary-foreground"
              aria-hidden
            >
              <ShieldCheck className="size-3.5" />
            </span>
            Evexía
          </Link>
          <Button asChild variant="ghost" size="sm">
            <Link to="/auth/login" search={EMPTY_AUTH_SEARCH}>
              Sign in
            </Link>
          </Button>
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto grid w-full max-w-6xl gap-16 px-6 py-16 lg:grid-cols-[1.2fr_1fr] lg:items-center lg:py-24">
          <div className="grid gap-6">
            <span className="inline-flex w-fit items-center gap-1.5 rounded-sm border border-border-subtle bg-surface px-2 py-1 font-mono text-xs uppercase tracking-wider text-fg-muted">
              EAP operations platform
            </span>
            <h1 className="text-4xl font-semibold tracking-tight text-fg md:text-5xl lg:text-6xl">
              Manage care, clients, and contracts with{' '}
              <span className="text-primary">clarity</span>.
            </h1>
            <p className="max-w-prose text-base leading-relaxed text-fg-muted md:text-lg">
              A single console for case managers and platform staff. Track
              sessions, monitor incidents, renew contracts, and stay
              audit-ready — all in one place.
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <Button asChild size="lg">
                <Link to="/auth/signup">
                  Get started
                  <ArrowUpRight className="size-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link to="/auth/login" search={EMPTY_AUTH_SEARCH}>
                  Sign in
                </Link>
              </Button>
            </div>
          </div>

          <FeatureSummary />
        </div>
      </main>

      <footer className="border-t border-border-subtle">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4 text-xs text-fg-subtle">
          <span>© 2026 Evexía</span>
          <span className="font-mono">v0.1</span>
        </div>
      </footer>
    </div>
  )
}

const FEATURES: ReadonlyArray<{ title: string; body: string }> = [
  {
    title: 'Client and contract lifecycle',
    body: 'Onboard organisations, manage tiers, renew agreements, and track every change in audit.',
  },
  {
    title: 'Sessions, cases, and incidents',
    body: 'Log delivered care, escalate critical incidents, route cases through review.',
  },
  {
    title: 'Insight without the spreadsheet',
    body: 'KPI dashboards, surveys, and engagement reports that stay in sync with the source.',
  },
]

function FeatureSummary() {
  return (
    <div className="grid gap-3 rounded-md border border-border-subtle bg-surface p-4 md:p-6">
      {FEATURES.map((f, i) => (
        <div key={f.title} className="grid gap-1">
          <div className="flex items-center gap-2">
            <span
              className="grid size-5 place-items-center rounded-sm bg-primary/10 font-mono text-[10px] font-medium text-primary"
              aria-hidden
            >
              {i + 1}
            </span>
            <h2 className="text-sm font-semibold text-fg">{f.title}</h2>
          </div>
          <p className="pl-7 text-sm text-fg-muted">{f.body}</p>
        </div>
      ))}
    </div>
  )
}
