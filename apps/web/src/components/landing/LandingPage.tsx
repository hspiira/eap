import { Link } from '@tanstack/react-router'
import { ArrowRight } from 'lucide-react'

import { Button } from '@/components/ui/button'

import { DutyLog } from './DutyLog'

const EMPTY_AUTH_SEARCH = {
  tenant_code: undefined,
  email: undefined,
  redirect: undefined,
} as const

const NAV = [
  { href: '#flow', label: 'How care moves' },
  { href: '#platform', label: 'The console' },
  { href: '#assurance', label: 'Assurance' },
]

const ASSURANCES: ReadonlyArray<{ term: string; detail: string }> = [
  { term: 'Role-scoped access', detail: 'Clinical notes stay with the clinicians who own them.' },
  { term: 'Immutable audit trail', detail: 'Every read, edit, and escalation, with who and when.' },
  { term: 'Single sign-on', detail: 'Corporate identity, enforced at the door.' },
  { term: 'No silent deletions', detail: 'Records are closed and archived, never quietly erased.' },
]

const STEPS: ReadonlyArray<{ step: string; title: string; detail: string }> = [
  {
    step: '01',
    title: 'Intake',
    detail:
      'A person calls, emails, or arrives by HR referral. One record from first contact, whichever door they came through.',
  },
  {
    step: '02',
    title: 'Triage',
    detail:
      'Risk and severity scored at intake, so the case that cannot wait is the one at the top of the worklist.',
  },
  {
    step: '03',
    title: 'Assignment',
    detail:
      'Matched to a counsellor or provider on language, location, and the caseload they are already carrying.',
  },
  {
    step: '04',
    title: 'Sessions',
    detail:
      'Delivered care logged against the client’s contract, so utilisation is a fact rather than a reconstruction.',
  },
  {
    step: '05',
    title: 'Closure',
    detail:
      'Outcomes recorded, the case closed, and the renewal pack drawn from the same records the clinicians wrote.',
  },
]

const CAPABILITIES: ReadonlyArray<{ title: string; detail: string; span?: boolean }> = [
  {
    title: 'Clients and contracts',
    detail:
      'Onboard organisations, set tiers and rates, and see a renewal window opening long before the agreement lapses.',
    span: true,
  },
  {
    title: 'Cases and incidents',
    detail:
      'Route cases through review, keep notes with the people entitled to read them, and escalate critical incidents on the clock.',
  },
  {
    title: 'Sessions and providers',
    detail:
      'Log delivered care, manage the counsellor network, and see who has capacity this week.',
  },
  {
    title: 'Insight and audit',
    detail:
      'KPIs, surveys, and engagement reports that read from the same records as the audit trail. No exports, no reconciliation.',
    span: true,
  },
]

export function LandingPage() {
  return (
    <div className="landing flex min-h-svh flex-col">
      <SiteHeader />

      <main className="flex-1">
        <Hero />
        <CareFlow />
        <Capabilities />
        <Assurance />
        <Closing />
      </main>

      <SiteFooter />
    </div>
  )
}

function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-(--lp-line-soft) bg-(--lp-page)/85 backdrop-blur-md">
      <div className="mx-auto flex w-full max-w-[80rem] items-center justify-between gap-6 px-5 py-3.5 md:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <img src="/evexía.svg" alt="" aria-hidden className="size-6 shrink-0" />
          <span className="lp-display text-lg tracking-[-0.02em]">Evexía</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex" aria-label="Sections">
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="text-sm text-(--lp-fg-muted) transition-colors hover:text-(--lp-fg)"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <Button
          asChild
          size="sm"
          className="h-9 rounded-full bg-(--lp-fg) px-4 text-(--lp-page) shadow-none hover:bg-(--lp-fg)/85"
        >
          <Link to="/auth/login" search={EMPTY_AUTH_SEARCH}>
            Sign in
          </Link>
        </Button>
      </div>
    </header>
  )
}

function Hero() {
  return (
    <section className="mx-auto w-full max-w-[80rem] px-5 pt-14 pb-8 md:px-8 md:pt-20">
      <h1 className="lp-display lp-rise text-[clamp(2.5rem,7.7vw,6.75rem)]">
        Care doesn’t keep
        <br />
        office hours.
      </h1>

      <div className="mt-8 grid gap-8 md:mt-10 lg:grid-cols-[minmax(0,44ch)_auto] lg:items-end lg:justify-between lg:gap-16">
        <p
          className="lp-lede lp-rise text-lg leading-[1.55] text-(--lp-fg-muted) md:text-xl"
          style={{ '--lp-delay': '0.1s' } as React.CSSProperties}
        >
          Neither does the console that runs it. Evexía holds an entire
          assistance programme: intake, triage, sessions, incidents, contracts,
          and the audit trail behind every decision.
        </p>

        <div
          className="lp-rise flex flex-wrap items-center gap-x-3 gap-y-3"
          style={{ '--lp-delay': '0.2s' } as React.CSSProperties}
        >
          <Button
            asChild
            size="lg"
            className="h-12 rounded-full bg-(--lp-brand) px-6 text-[15px] text-(--lp-page) shadow-none hover:bg-(--lp-brand)/90"
          >
            <Link to="/auth/login" search={EMPTY_AUTH_SEARCH}>
              Sign in to the console
              <ArrowRight className="size-4" />
            </Link>
          </Button>
          <Button
            asChild
            variant="ghost"
            size="lg"
            className="h-12 rounded-full px-5 text-[15px] text-(--lp-fg) hover:bg-(--lp-wash)"
          >
            <a href="#flow">See how care moves</a>
          </Button>
        </div>
      </div>

      <div className="relative mt-12 md:mt-16">
        <DutyLog />
        <ProofBar />
      </div>
    </section>
  )
}

const PROOF: ReadonlyArray<{ value: string; label: string }> = [
  { value: '24/7', label: 'Intake, every hour of the day' },
  { value: 'One record', label: 'From first contact to closure' },
  { value: 'Every action', label: 'Written to the audit trail' },
]

function ProofBar() {
  return (
    <div
      className="lp-rise relative z-10 mx-3 mt-3 rounded-md bg-(--lp-card) p-1.5 sm:mx-6 sm:-mt-16 md:mx-10"
      style={{ '--lp-delay': '1.75s' } as React.CSSProperties}
    >
      <dl className="grid divide-y divide-(--lp-line-soft) sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        {PROOF.map((item) => (
          <div key={item.value} className="flex flex-col gap-0.5 px-5 py-3">
            <dt className="lp-display text-base tracking-[-0.02em]">{item.value}</dt>
            <dd className="text-[13px] text-(--lp-fg-muted)">{item.label}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

function CareFlow() {
  return (
    <section id="flow" className="scroll-mt-20 border-t border-(--lp-line-soft) py-20 md:py-28">
      <div className="mx-auto w-full max-w-[80rem] px-5 md:px-8">
        <h2 className="lp-display max-w-[52rem] text-[clamp(2rem,4.2vw,3.5rem)]">
          How care moves through the console
        </h2>

        <ol className="mt-12 grid gap-px border-t border-(--lp-line) md:mt-16 md:grid-cols-5 md:gap-0">
          {STEPS.map((item) => (
            <li
              key={item.step}
              className="grid content-start gap-3 border-b border-(--lp-line-soft) py-6 md:border-b-0 md:border-r md:border-r-(--lp-line-soft) md:px-6 md:py-8 md:first:pl-0 md:last:border-r-0 md:last:pr-0"
            >
              <span className="lp-mono text-[11px] text-(--lp-brand)">{item.step}</span>
              <h3 className="lp-display text-xl tracking-[-0.02em]">{item.title}</h3>
              <p className="text-[15px] leading-relaxed text-(--lp-fg-muted)">
                {item.detail}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

function Capabilities() {
  return (
    <section id="platform" className="scroll-mt-20 bg-(--lp-wash) py-20 md:py-28">
      <div className="mx-auto w-full max-w-[80rem] px-5 md:px-8">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <h2 className="lp-display max-w-[44rem] text-[clamp(2rem,4.2vw,3.5rem)]">
            Four surfaces, one set of records
          </h2>
          <p className="max-w-[30ch] text-[15px] leading-relaxed text-(--lp-fg-muted)">
            Case managers, programme leads, and platform staff work the same data
            from different angles.
          </p>
        </div>

        <div className="mt-12 grid gap-4 md:mt-16 md:grid-cols-3">
          {CAPABILITIES.map((item) => (
            <article
              key={item.title}
              className={`grid content-start gap-3 rounded-md bg-(--lp-card) p-6 md:p-8 ${
                item.span ? 'md:col-span-2' : ''
              }`}
            >
              <h3 className="lp-display text-2xl tracking-[-0.025em]">{item.title}</h3>
              <p className="max-w-[46ch] text-[15px] leading-relaxed text-(--lp-fg-muted)">
                {item.detail}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

function Assurance() {
  return (
    <section id="assurance" className="scroll-mt-20 bg-(--lp-panel) py-20 text-(--lp-panel-fg) md:py-28">
      <div className="mx-auto grid w-full max-w-[80rem] gap-12 px-5 md:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)] lg:gap-20">
        <div>
          <h2 className="lp-display text-[clamp(2rem,4vw,3.25rem)]">
            The most sensitive records a workplace holds
          </h2>
          <p className="mt-6 max-w-[42ch] text-[15px] leading-relaxed text-(--lp-panel-muted)">
            An assistance programme only works while people trust it with what
            they would tell no one else. Access is scoped to the people doing
            the work, and every movement of a record is logged.
          </p>
        </div>

        <dl className="grid gap-px self-start border-t border-(--lp-panel-line) sm:grid-cols-2">
          {ASSURANCES.map((item) => (
            <div
              key={item.term}
              className="grid content-start gap-2 border-b border-(--lp-panel-line) py-6 sm:px-6 sm:first:pl-0 sm:[&:nth-child(2n)]:pr-0 sm:[&:nth-child(2n+1)]:pl-0"
            >
              <dt className="lp-display text-lg tracking-[-0.02em]">{item.term}</dt>
              <dd className="text-sm leading-relaxed text-(--lp-panel-muted)">
                {item.detail}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  )
}

function Closing() {
  return (
    <section className="mx-auto w-full max-w-[80rem] px-5 py-20 md:px-8 md:py-28">
      <div className="flex flex-wrap items-end justify-between gap-8">
        <h2 className="lp-display max-w-[24ch] text-[clamp(2rem,4.4vw,3.75rem)]">
          Pick up the programme where you left it.
        </h2>
        <Button
          asChild
          size="lg"
          className="h-12 rounded-full bg-(--lp-brand) px-6 text-[15px] text-(--lp-page) shadow-none hover:bg-(--lp-brand)/90"
        >
          <Link to="/auth/login" search={EMPTY_AUTH_SEARCH}>
            Sign in
            <ArrowRight className="size-4" />
          </Link>
        </Button>
      </div>
    </section>
  )
}

function SiteFooter() {
  return (
    <footer className="border-t border-(--lp-line-soft)">
      <div className="mx-auto flex w-full max-w-[80rem] flex-wrap items-center justify-between gap-4 px-5 py-6 md:px-8">
        <div className="flex items-center gap-2.5">
          <img src="/evexía.svg" alt="" aria-hidden className="size-5 shrink-0" />
          <span className="text-sm text-(--lp-fg-muted)">
            © 2026 Evexía, a Minet company
          </span>
        </div>
        <span className="lp-mono text-[11px] text-(--lp-fg-muted)">v0.1</span>
      </div>
    </footer>
  )
}
