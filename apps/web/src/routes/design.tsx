import { useState } from 'react'

import { createFileRoute } from '@tanstack/react-router'
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  FileSignature,
  MessageSquare,
} from 'lucide-react'

import {
  ActivityFeedCard,
  type Activity,
} from '@/components/ActivityFeedCard'
import { ClientAlertsCard, type ClientAlert } from '@/components/ClientAlertsCard'
import { OnboardingProgressCard } from '@/components/OnboardingProgressCard'
import { GalleryControls } from '@/components/gallery/GalleryControls'
import { GallerySection, GallerySpecimen } from '@/components/gallery/GallerySection'
import { ProviderTierBadge } from '@/components/common/ProviderTierBadge'
import { SeverityBadge } from '@/components/common/SeverityBadge'
import { StatusBadge } from '@/components/common/StatusBadge'
import { TierBadge } from '@/components/common/TierBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { ClientTier, IncidentSeverity, ProviderTier } from '@/types/enums'

export const Route = createFileRoute('/design')({
  component: GalleryRoute,
})

type Density = 'compact' | 'comfortable'

function GalleryRoute() {
  const [density, setDensity] = useState<Density>('compact')

  return (
    <div data-density={density} className="min-h-svh bg-bg text-fg">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <GalleryControls density={density} onDensityChange={setDensity} />

        <nav aria-label="Gallery sections" className="mb-8 flex flex-wrap gap-2">
          {SECTIONS.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className="rounded-sm border border-border-subtle px-2.5 py-1 text-xs text-fg-muted transition-colors hover:border-border hover:text-fg"
            >
              {s.label}
            </a>
          ))}
        </nav>

        <ColorTokens />
        <TypographyTokens />
        <SpacingAndRadius />
        <ButtonsSpecimen />
        <BadgesSpecimen />
        <DomainBadgesSpecimen />
        <CardsSpecimen />
        <MigratedCardsSpecimen />
        <FormsSpecimen />
        <FeedbackSpecimen />
        <ComponentRegistry />
      </div>
    </div>
  )
}

const SECTIONS = [
  { id: 'colors', label: 'Colors' },
  { id: 'typography', label: 'Typography' },
  { id: 'spacing', label: 'Spacing & Radius' },
  { id: 'buttons', label: 'Buttons' },
  { id: 'badges', label: 'Badges' },
  { id: 'domain-badges', label: 'Domain Badges' },
  { id: 'cards', label: 'Cards' },
  { id: 'migrated-cards', label: 'Migrated Cards' },
  { id: 'forms', label: 'Forms' },
  { id: 'feedback', label: 'Feedback' },
  { id: 'registry', label: 'Registry' },
] as const

function ColorTokens() {
  const surfaces = [
    'bg',
    'surface',
    'surface-hover',
    'surface-elevated',
  ] as const
  const fgs = ['fg', 'fg-muted', 'fg-subtle'] as const
  const borders = ['border', 'border-subtle', 'border-strong'] as const
  const semantic = [
    'brand',
    'brand-hover',
    'brand-soft',
    'success',
    'success-soft',
    'warning',
    'warning-soft',
    'danger',
    'danger-soft',
    'info',
    'info-soft',
  ] as const

  return (
    <GallerySection
      id="colors"
      title="Colors"
      description="Semantic tokens. Components consume these — never raw hex, never palette names."
    >
      <GallerySpecimen label="Surfaces" source="--color-bg / --color-surface / ...">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {surfaces.map((name) => (
            <Swatch key={name} name={name} className={`bg-${name}`} kind="surface" />
          ))}
        </div>
      </GallerySpecimen>
      <GallerySpecimen label="Foreground" source="--color-fg / --color-fg-muted / --color-fg-subtle">
        <div className="grid grid-cols-3 gap-3">
          {fgs.map((name) => (
            <div
              key={name}
              className="rounded-sm border border-border bg-surface p-3"
            >
              <p className={`text-${name}`}>The quick brown fox</p>
              <p className="mt-1 font-mono text-xs text-fg-subtle">--color-{name}</p>
            </div>
          ))}
        </div>
      </GallerySpecimen>
      <GallerySpecimen label="Borders">
        <div className="grid grid-cols-3 gap-3">
          {borders.map((name) => (
            <div
              key={name}
              className={`rounded-sm border-2 border-${name} bg-surface p-3`}
            >
              <p className="text-sm text-fg">--color-{name}</p>
            </div>
          ))}
        </div>
      </GallerySpecimen>
      <GallerySpecimen label="Semantic" source="brand / success / warning / danger / info">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {semantic.map((name) => (
            <Swatch key={name} name={name} className={`bg-${name}`} kind="semantic" />
          ))}
        </div>
      </GallerySpecimen>
    </GallerySection>
  )
}

function Swatch({
  name,
  className,
  kind,
}: {
  name: string
  className: string
  kind: 'surface' | 'semantic'
}) {
  return (
    <div className="overflow-hidden rounded-sm border border-border">
      <div className={`${className} h-12`} />
      <div className="bg-surface px-2 py-1.5">
        <p className="text-xs font-medium text-fg">{name}</p>
        <p className="font-mono text-[10px] text-fg-subtle">
          --color-{name}
          {kind === 'semantic' ? '' : ''}
        </p>
      </div>
    </div>
  )
}

function TypographyTokens() {
  const sizes = [
    { name: 'xs', cls: 'text-xs', label: '11px' },
    { name: 'sm', cls: 'text-sm', label: '12px' },
    { name: 'base', cls: 'text-base', label: '13px' },
    { name: 'md', cls: 'text-[14px]', label: '14px' },
    { name: 'lg', cls: 'text-lg', label: '16px' },
    { name: 'xl', cls: 'text-xl', label: '18px' },
    { name: '2xl', cls: 'text-2xl', label: '22px' },
  ] as const

  return (
    <GallerySection
      id="typography"
      title="Typography"
      description="Type scale + tabular numerics. Mono is reserved for IDs, dates, and counts."
    >
      <GallerySpecimen label="Scale" source="--font-size-*">
        <div className="grid gap-2">
          {sizes.map((s) => (
            <div key={s.name} className="flex items-baseline gap-4">
              <code className="w-16 font-mono text-xs text-fg-subtle">{s.name}</code>
              <code className="w-12 font-mono text-xs text-fg-muted">{s.label}</code>
              <p className={`${s.cls} text-fg`}>The quick brown fox jumps over the lazy dog</p>
            </div>
          ))}
        </div>
      </GallerySpecimen>
      <GallerySpecimen label="Tabular numerics" source="font-mono + font-feature-settings: 'tnum'">
        <div className="grid gap-2 font-mono tabular-nums text-fg">
          <div className="flex justify-between border-b border-border-subtle py-1">
            <span>Active clients</span>
            <span>1,234</span>
          </div>
          <div className="flex justify-between border-b border-border-subtle py-1">
            <span>Sessions this month</span>
            <span>87,651</span>
          </div>
          <div className="flex justify-between py-1">
            <span>Avg. response time</span>
            <span>00:08:42</span>
          </div>
        </div>
      </GallerySpecimen>
    </GallerySection>
  )
}

function SpacingAndRadius() {
  return (
    <GallerySection
      id="spacing"
      title="Spacing & Radius"
      description="4px base, three radii (none/sm/md), three shadows (none/sm/md)."
    >
      <GallerySpecimen label="Spacing">
        <div className="flex items-end gap-2">
          {[1, 2, 3, 4, 6, 8].map((n) => (
            <div key={n} className="grid place-items-center gap-1">
              <div
                className="bg-brand"
                style={{ width: n * 4, height: n * 4 }}
                aria-hidden
              />
              <code className="font-mono text-[10px] text-fg-subtle">space-{n}</code>
              <code className="font-mono text-[10px] text-fg-subtle">{n * 4}px</code>
            </div>
          ))}
        </div>
      </GallerySpecimen>
      <GallerySpecimen label="Radius">
        <div className="flex gap-3">
          <div className="grid place-items-center gap-1">
            <div className="rounded-none h-12 w-16 border border-border bg-surface" />
            <code className="font-mono text-[10px] text-fg-subtle">none / 0</code>
          </div>
          <div className="grid place-items-center gap-1">
            <div className="rounded-sm h-12 w-16 border border-border bg-surface" />
            <code className="font-mono text-[10px] text-fg-subtle">sm / 4px</code>
          </div>
          <div className="grid place-items-center gap-1">
            <div className="rounded-md h-12 w-16 border border-border bg-surface" />
            <code className="font-mono text-[10px] text-fg-subtle">md / 6px</code>
          </div>
        </div>
      </GallerySpecimen>
    </GallerySection>
  )
}

function ButtonsSpecimen() {
  return (
    <GallerySection
      id="buttons"
      title="Buttons"
      description="Current shadcn Button — forked, missing outline/destructive variants. Reset planned in this phase."
    >
      <GallerySpecimen label="Variants">
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="default">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button disabled>Disabled</Button>
        </div>
      </GallerySpecimen>
      <GallerySpecimen label="Sizes">
        <div className="flex flex-wrap items-center gap-3">
          <Button size="sm">Small</Button>
          <Button size="default">Default</Button>
          <Button size="lg">Large</Button>
        </div>
      </GallerySpecimen>
    </GallerySection>
  )
}

function BadgesSpecimen() {
  return (
    <GallerySection id="badges" title="Badges" description="shadcn Badge primitive (forked).">
      <GallerySpecimen label="Variants">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="default">Default</Badge>
          <Badge variant="secondary">Secondary</Badge>
          <Badge variant="outline">Outline</Badge>
        </div>
      </GallerySpecimen>
      <GallerySpecimen label="Sizes">
        <div className="flex flex-wrap items-center gap-2">
          <Badge size="sm">Small</Badge>
          <Badge size="default">Default</Badge>
          <Badge size="lg">Large</Badge>
        </div>
      </GallerySpecimen>
    </GallerySection>
  )
}

function DomainBadgesSpecimen() {
  return (
    <GallerySection
      id="domain-badges"
      title="Domain Badges"
      description="EAP-specific badges. To be reviewed against the new token system."
    >
      <GallerySpecimen label="StatusBadge" source="components/common/StatusBadge.tsx">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status="active" />
          <StatusBadge status="pending" />
          <StatusBadge status="archived" />
          <StatusBadge status="terminated" />
        </div>
      </GallerySpecimen>
      <GallerySpecimen label="TierBadge" source="components/common/TierBadge.tsx">
        <div className="flex flex-wrap items-center gap-2">
          <TierBadge tier={ClientTier.A} />
          <TierBadge tier={ClientTier.B} />
          <TierBadge tier={ClientTier.C} />
          <TierBadge tier={null} />
        </div>
      </GallerySpecimen>
      <GallerySpecimen label="SeverityBadge" source="components/common/SeverityBadge.tsx">
        <div className="flex flex-wrap items-center gap-2">
          <SeverityBadge severity={IncidentSeverity.LOW} />
          <SeverityBadge severity={IncidentSeverity.MEDIUM} />
          <SeverityBadge severity={IncidentSeverity.HIGH} />
          <SeverityBadge severity={IncidentSeverity.CRITICAL} />
        </div>
      </GallerySpecimen>
      <GallerySpecimen label="ProviderTierBadge" source="components/common/ProviderTierBadge.tsx">
        <div className="flex flex-wrap items-center gap-2">
          <ProviderTierBadge tier={ProviderTier.T1} />
          <ProviderTierBadge tier={ProviderTier.T2} />
          <ProviderTierBadge tier={ProviderTier.T3} />
        </div>
      </GallerySpecimen>
    </GallerySection>
  )
}

function CardsSpecimen() {
  return (
    <GallerySection id="cards" title="Cards" description="shadcn Card primitive — base for all card-shaped surfaces.">
      <GallerySpecimen label="Card">
        <Card>
          <CardHeader>
            <CardTitle>Active engagements</CardTitle>
            <CardDescription>87 open across 12 client organisations.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-fg-muted">
              Card body content. Use this primitive for every card-shaped surface;
              do not roll your own div + border.
            </p>
          </CardContent>
          <CardFooter>
            <Button size="sm">View all</Button>
          </CardFooter>
        </Card>
      </GallerySpecimen>
    </GallerySection>
  )
}

function MigratedCardsSpecimen() {
  return (
    <GallerySection
      id="migrated-cards"
      title="Migrated Cards"
      description="Cards rebuilt against shadcn primitives + new tokens. Reference for the rest of the migration."
    >
      <GallerySpecimen
        label="ActivityFeedCard"
        source="components/ActivityFeedCard.tsx"
      >
        <div className="max-w-md">
          <ActivityFeedCard activities={GALLERY_ACTIVITIES} />
        </div>
      </GallerySpecimen>
      <GallerySpecimen
        label="OnboardingProgressCard"
        source="components/OnboardingProgressCard.tsx"
      >
        <div className="max-w-md">
          <OnboardingProgressCard
            onDismiss={() => {}}
            onStartStep={() => {}}
          />
        </div>
      </GallerySpecimen>
      <GallerySpecimen
        label="ClientAlertsCard"
        source="components/ClientAlertsCard.tsx"
      >
        <div className="grid max-w-md gap-3">
          <ClientAlertsCard alerts={GALLERY_ALERTS} />
          <ClientAlertsCard alerts={[]} />
        </div>
      </GallerySpecimen>
    </GallerySection>
  )
}

const GALLERY_ACTIVITIES: Activity[] = [
  {
    id: "g1",
    icon: CalendarClock,
    tone: "info",
    title: "Weekly summary",
    description: "12 sessions delivered, 3 case openings, 1 critical incident.",
    time: "Today",
    badge: { label: "Cycle complete", variant: "secondary" },
  },
  {
    id: "g2",
    icon: FileSignature,
    tone: "warning",
    title: "Contract renewal due",
    description: "Acme Holdings — current term expires in 14 days.",
    time: "Yesterday",
  },
  {
    id: "g3",
    icon: AlertTriangle,
    tone: "danger",
    title: "Critical incident logged",
    description: "Severity: High. Awaiting case-manager assignment.",
    time: "Yesterday",
    badge: { label: "Action needed", variant: "destructive" },
  },
  {
    id: "g4",
    icon: CheckCircle2,
    tone: "success",
    title: "Survey completed",
    description: "12 respondents over the past 24 hours.",
    time: "2d ago",
  },
  {
    id: "g5",
    icon: MessageSquare,
    tone: "info",
    title: "New thread",
    description: "Care manager replied to engagement #4221.",
    time: "3d ago",
  },
]

const GALLERY_ALERTS: ClientAlert[] = [
  {
    id: "a1",
    title: "Contract renewal overdue",
    severity: "high",
    description:
      "Acme Holdings master service agreement lapsed 3 days ago. Sessions are paused until renewed.",
    link: "/contracts",
    linkLabel: "Open contracts",
  },
  {
    id: "a2",
    title: "Critical incident pending review",
    severity: "critical",
    description:
      "Severity High incident reported 2025-05-08. Awaiting case-manager assignment.",
  },
  {
    id: "a3",
    title: "Survey response rate below target",
    severity: "medium",
  },
  {
    id: "a4",
    title: "Quarterly check-in scheduled",
    severity: "low",
  },
]

function FormsSpecimen() {
  return (
    <GallerySection id="forms" title="Forms" description="Inputs and labels — pair with react-hook-form + zod (Phase 4).">
      <GallerySpecimen label="Input + Label">
        <div className="grid max-w-sm gap-3">
          <div className="grid gap-1.5">
            <Label htmlFor="g-name">Full name</Label>
            <Input id="g-name" placeholder="Jane Doe" />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="g-email">Work email</Label>
            <Input id="g-email" type="email" placeholder="jane@example.com" />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="g-disabled">Disabled</Label>
            <Input id="g-disabled" disabled value="Read-only field" />
          </div>
        </div>
      </GallerySpecimen>
    </GallerySection>
  )
}

function FeedbackSpecimen() {
  return (
    <GallerySection id="feedback" title="Feedback" description="Skeletons and separators.">
      <GallerySpecimen label="Skeleton">
        <div className="grid gap-2">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-64" />
          <Skeleton className="h-4 w-32" />
        </div>
      </GallerySpecimen>
      <GallerySpecimen label="Separator">
        <div className="grid gap-3">
          <p className="text-sm text-fg">Above</p>
          <Separator />
          <p className="text-sm text-fg">Below</p>
        </div>
      </GallerySpecimen>
    </GallerySection>
  )
}

const REGISTRY: ReadonlyArray<{
  group: string
  items: ReadonlyArray<{ name: string; path: string; status: 'review' | 'migrate' | 'rebuild' | 'audit' }>
}> = [
  {
    group: 'Layout',
    items: [
      { name: 'AppLayout', path: 'components/AppLayout.tsx', status: 'rebuild' },
      { name: 'AppSidebar', path: 'components/AppSidebar.tsx', status: 'rebuild' },
      { name: 'DashboardHeader', path: 'components/DashboardHeader.tsx', status: 'rebuild' },
      { name: 'DashboardMain', path: 'components/DashboardMain.tsx', status: 'audit' },
    ],
  },
  {
    group: 'Dashboard cards (review for EAP fit)',
    items: [
      { name: 'ApexIntroCard', path: 'components/ApexIntroCard.tsx', status: 'review' },
      { name: 'ActivityFeedCard', path: 'components/ActivityFeedCard.tsx', status: 'audit' },
      { name: 'ChartAreaInteractive', path: 'components/ChartAreaInteractive.tsx', status: 'audit' },
      { name: 'EmailCampaignCard', path: 'components/EmailCampaignCard.tsx', status: 'review' },
      { name: 'EventCards', path: 'components/EventCards.tsx', status: 'audit' },
      { name: 'FlightProgressCard', path: 'components/FlightProgressCard.tsx', status: 'review' },
      { name: 'HRDashboard', path: 'components/HRDashboard.tsx', status: 'audit' },
      { name: 'InviteToProjectCard', path: 'components/InviteToProjectCard.tsx', status: 'audit' },
      { name: 'LoggedInDevicesCard', path: 'components/LoggedInDevicesCard.tsx', status: 'review' },
      { name: 'MapSettingsCard', path: 'components/MapSettingsCard.tsx', status: 'review' },
      { name: 'NotificationsCard', path: 'components/NotificationsCard.tsx', status: 'audit' },
      { name: 'OnSiteBehaviorCard', path: 'components/OnSiteBehaviorCard.tsx', status: 'review' },
      { name: 'OnboardingProgressCard', path: 'components/OnboardingProgressCard.tsx', status: 'audit' },
      { name: 'QueryInputCard', path: 'components/QueryInputCard.tsx', status: 'audit' },
      { name: 'TransitionsCard', path: 'components/TransitionsCard.tsx', status: 'audit' },
    ],
  },
  {
    group: 'Client cards',
    items: [
      { name: 'ClientActivityCard', path: 'components/ClientActivityCard.tsx', status: 'audit' },
      { name: 'ClientAlertsCard', path: 'components/ClientAlertsCard.tsx', status: 'audit' },
      { name: 'ClientOnboardingCard', path: 'components/ClientOnboardingCard.tsx', status: 'audit' },
      { name: 'ClientStaffSummaryCard', path: 'components/ClientStaffSummaryCard.tsx', status: 'audit' },
      { name: 'ClientTodaysTodoCard', path: 'components/ClientTodaysTodoCard.tsx', status: 'audit' },
      { name: 'ClientUpcomingCard', path: 'components/ClientUpcomingCard.tsx', status: 'audit' },
      { name: 'IndustryDetailsCard', path: 'components/IndustryDetailsCard.tsx', status: 'migrate' },
    ],
  },
  {
    group: 'Page headers & skeletons',
    items: [
      { name: 'ClientsPageHeader', path: 'components/ClientsPageHeader.tsx', status: 'rebuild' },
      { name: 'ClientsPageSkeletons', path: 'components/ClientsPageSkeletons.tsx', status: 'rebuild' },
      { name: 'IndustriesPageHeader', path: 'components/IndustriesPageHeader.tsx', status: 'rebuild' },
      { name: 'IndustriesPageSkeletons', path: 'components/IndustriesPageSkeletons.tsx', status: 'rebuild' },
      { name: 'TagsPageHeader', path: 'components/TagsPageHeader.tsx', status: 'rebuild' },
    ],
  },
  {
    group: 'Forms',
    items: [
      { name: 'ClientForm', path: 'components/ClientForm.tsx', status: 'rebuild' },
    ],
  },
  {
    group: 'Common (keep & migrate to tokens)',
    items: [
      { name: 'ConfirmDialog', path: 'components/common/ConfirmDialog.tsx', status: 'migrate' },
      { name: 'DataTable', path: 'components/common/DataTable.tsx', status: 'rebuild' },
      { name: 'DiagnosisSelector', path: 'components/common/DiagnosisSelector.tsx', status: 'migrate' },
      { name: 'FormField', path: 'components/common/FormField.tsx', status: 'rebuild' },
      { name: 'LifecycleActions', path: 'components/common/LifecycleActions.tsx', status: 'migrate' },
      { name: 'PricingConfig', path: 'components/common/PricingConfig.tsx', status: 'migrate' },
      { name: 'QueryTable', path: 'components/common/QueryTable.tsx', status: 'rebuild' },
    ],
  },
  {
    group: 'Care callbacks & surveys',
    items: [
      { name: 'CrisisAlert', path: 'components/care-callbacks/CrisisAlert.tsx', status: 'migrate' },
      { name: 'QuestionnaireRenderer', path: 'components/care-callbacks/QuestionnaireRenderer.tsx', status: 'migrate' },
      { name: 'WebhookSetupHelper', path: 'components/surveys/WebhookSetupHelper.tsx', status: 'migrate' },
    ],
  },
]

const STATUS_TONE: Record<'review' | 'migrate' | 'rebuild' | 'audit', string> = {
  review: 'border-warning/40 bg-warning-soft text-warning-fg',
  migrate: 'border-info/40 bg-info-soft text-info-fg',
  rebuild: 'border-danger/40 bg-danger-soft text-danger-fg',
  audit: 'border-fg-subtle/40 bg-surface-hover text-fg-muted',
}

const STATUS_COPY: Record<'review' | 'migrate' | 'rebuild' | 'audit', string> = {
  review: 'Review (template residue suspected)',
  migrate: 'Migrate to new tokens',
  rebuild: 'Rebuild against shadcn',
  audit: 'Audit hardcoded content',
}

function ComponentRegistry() {
  return (
    <GallerySection
      id="registry"
      title="Component Registry"
      description="Every component file in src/components, with a migration disposition. Specimens for these land here as each is migrated."
    >
      <div className="grid gap-1.5 text-xs">
        <div className="flex flex-wrap gap-2">
          {(['review', 'migrate', 'rebuild', 'audit'] as const).map((s) => (
            <span
              key={s}
              className={`inline-flex items-center rounded-sm border px-2 py-0.5 ${STATUS_TONE[s]}`}
            >
              {STATUS_COPY[s]}
            </span>
          ))}
        </div>
      </div>
      <div className="grid gap-6">
        {REGISTRY.map((group) => (
          <div key={group.group} className="grid gap-2">
            <h3 className="text-sm font-semibold text-fg">{group.group}</h3>
            <ul className="grid gap-1">
              {group.items.map((item) => (
                <li
                  key={item.path}
                  className="flex items-center justify-between rounded-sm border border-border-subtle bg-surface px-3 py-2"
                >
                  <div className="flex items-baseline gap-3">
                    <span className="text-sm font-medium text-fg">{item.name}</span>
                    <code className="font-mono text-xs text-fg-subtle">{item.path}</code>
                  </div>
                  <span
                    className={`inline-flex items-center rounded-sm border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${STATUS_TONE[item.status]}`}
                  >
                    {item.status}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </GallerySection>
  )
}
