import { useCallback, useEffect, useState } from "react"

import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  BadgeCheck,
  Pencil,
  RotateCw,
  ShieldCheck,
  ShieldOff,
  UserCog,
} from "lucide-react"

import { personsApi } from "@/api/endpoints/persons"
import { usersApi } from "@/api/endpoints/users"
import { EmptyState } from "@/components/common/EmptyState"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { Button } from "@/components/ui/button"
import { UserFormSheet } from "@/components/UserFormSheet"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { cn } from "@/lib/utils"
import type { Person, User } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/users/$userId")({
  component: UserDetailPage,
})

type TabValue = "overview" | "security" | "preferences" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "security", "preferences", "history"]

function UserDetailPage() {
  const { userId } = Route.useParams()
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [person, setPerson] = useState<Person | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [editOpen, setEditOpen] = useState(false)

  const fetchUser = useCallback(async () => {
    try {
      setLoading(true)
      setUser(await usersApi.getById(userId))
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  useEffect(() => {
    if (!user) {
      setPerson(null)
      return
    }
    let cancelled = false
    personsApi
      .getByUserId(user.id)
      .then((p) => {
        if (!cancelled) setPerson(p)
      })
      .catch(() => {
        if (!cancelled) setPerson(null)
      })
    return () => {
      cancelled = true
    }
  }, [user])

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      setActionLoading(true)
      try {
        if (action === "activate") await usersApi.activate(id)
        else if (action === "suspend") await usersApi.suspend(id)
        else if (action === "ban") await usersApi.ban(id)
        else if (action === "terminate") await usersApi.terminate(id, "Terminated from UI")
        else if (action === "deactivate") await usersApi.deactivate(id)
        await fetchUser()
      } finally {
        setActionLoading(false)
      }
    },
    [fetchUser],
  )

  if (loading) {
    return (
      <PageShell icon={UserCog} breadcrumb="People · Platform Users · …">
        <div className="min-h-0 flex-1 overflow-auto p-5">
          <DetailSkeleton />
        </div>
      </PageShell>
    )
  }

  if (!user) {
    return (
      <PageShell icon={UserCog} breadcrumb="People · Platform Users · Not found">
        <EmptyState
          icon={UserCog}
          title="User not found"
          description="They may have been terminated or never existed."
          action={
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => navigate({ to: "/users" })}
            >
              <ArrowLeft className="size-4" />
              Back to users
            </Button>
          }
        />
      </PageShell>
    )
  }

  return (
    <PageShell
      icon={UserCog}
      breadcrumb={`People · Platform Users · ${user.email}`}
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/users" })}
            aria-label="Back to users"
            title="Back to users"
            className="size-7 p-0 text-fg/70"
          >
            <ArrowLeft className="size-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={fetchUser}
            aria-label="Refresh"
            title="Refresh"
            className="size-7 p-0 text-fg/70"
            >
            <RotateCw className="size-3.5" />
            </Button>
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button
            size="sm"
            variant="outline"
            className="h-7 gap-1.5 px-2.5"
            onClick={() => setEditOpen(true)}
          >
            <Pencil className="size-3.5" />
            Edit
          </Button>
        </>
      }
    >
      <Hero user={user} />

      <UserFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        user={user}
        onSaved={(updated) => setUser(updated)}
      />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="security">Security</Tab>
                <Tab value="preferences">Preferences</Tab>
                <Tab value="history">History</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Account">
                    <DetailGrid>
                      <DetailRow label="Email" value={user.email} fullWidth />
                      <DetailRow label="Status" value={<StatusBadge status={user.status} />} />
                      <DetailRow
                        label="Active"
                        value={user.is_active ? "Yes" : "No"}
                      />
                      <DetailRow
                        label="Last login"
                        value={
                          user.last_login_at
                            ? new Date(user.last_login_at).toLocaleString()
                            : null
                        }
                      />
                      <DetailRow
                        label="Status changed"
                        value={
                          user.status_changed_at
                            ? new Date(user.status_changed_at).toLocaleString()
                            : null
                        }
                      />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Identity">
                    {person ? (
                      <Link
                        to="/persons/$personId"
                        params={{ personId: person.id }}
                        className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2 transition-colors hover:border-fg/25"
                      >
                        <span
                          aria-hidden
                          className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
                        >
                          {personInitial(person)}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-fg">
                            {person.first_name} {person.last_name}
                          </p>
                          <p className="truncate text-[11px] text-fg/55">
                            {person.person_type}
                          </p>
                        </div>
                      </Link>
                    ) : (
                      <p className="text-xs text-fg/55">
                        No person profile linked to this account.
                      </p>
                    )}
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="security">
                <DetailCard title="Email">
                  <DetailGrid>
                    <DetailRow
                      label="Verified"
                      value={
                        user.is_email_verified ? (
                          <span className="inline-flex items-center gap-1 text-fg">
                            <BadgeCheck className="size-3.5 text-primary" /> Yes
                          </span>
                        ) : (
                          <span className="text-fg/55">No</span>
                        )
                      }
                    />
                    <DetailRow
                      label="Verified at"
                      value={
                        user.email_verified_at
                          ? new Date(user.email_verified_at).toLocaleString()
                          : null
                      }
                    />
                  </DetailGrid>
                </DetailCard>

                <div className="mt-4">
                  <DetailCard title="Two-factor authentication">
                    <DetailGrid>
                      <DetailRow
                        label="Status"
                        value={
                          user.is_two_factor_enabled ? (
                            <span className="inline-flex items-center gap-1 text-fg">
                              <ShieldCheck className="size-3.5 text-primary" /> Enabled
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-fg/55">
                              <ShieldOff className="size-3.5" /> Disabled
                            </span>
                          )
                        }
                      />
                    </DetailGrid>
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="preferences">
                <DetailCard title="Locale">
                  <DetailGrid>
                    <DetailRow label="Language" value={user.preferred_language} />
                    <DetailRow label="Timezone" value={user.timezone} />
                    <DetailRow label="Date format" value={user.date_format} />
                    <DetailRow label="Week starts on" value={user.week_starts_on} />
                  </DetailGrid>
                </DetailCard>
                <div className="mt-4">
                  <DetailCard title="Notifications">
                    <DetailGrid>
                      <DetailRow
                        label="Email notifications"
                        value={user.email_notifications ? "On" : "Off"}
                      />
                      <DetailRow
                        label="Assignment alerts"
                        value={user.assignment_alerts ? "On" : "Off"}
                      />
                      <DetailRow
                        label="Session reminders"
                        value={user.session_reminders ? "On" : "Off"}
                      />
                      <DetailRow
                        label="Weekly digest"
                        value={user.weekly_digest ? "On" : "Off"}
                      />
                    </DetailGrid>
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="history">
                <EmptyState
                  title="No activity yet"
                  description="Sign-in events and security changes will appear here once the audit feed is wired up."
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              user={user}
              person={person}
              onAction={handleAction}
              actionLoading={actionLoading}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function Hero({ user }: { user: User }) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <UserCog className="size-4" />
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {user.email}
      </h1>
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <StatusBadge status={user.status} />
      {user.is_email_verified ? (
        <span className="inline-flex items-center gap-1 rounded-sm border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-[11px] font-medium text-primary">
          <BadgeCheck className="size-3" />
          Verified
        </span>
      ) : null}
      {user.is_two_factor_enabled ? (
        <span className="inline-flex items-center gap-1 rounded-sm border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-[11px] font-medium text-primary">
          <ShieldCheck className="size-3" />
          2FA
        </span>
      ) : null}
    </div>
  )
}

interface DetailRailProps {
  user: User
  person: Person | null
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
}

function DetailRail({ user, person, onAction, actionLoading }: DetailRailProps) {
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <div className="grid grid-cols-2 gap-3">
          <Stat
            label="2FA"
            value={
              user.is_two_factor_enabled ? (
                <span className="text-primary">On</span>
              ) : (
                "Off"
              )
            }
          />
          <Stat
            label="Email"
            value={user.is_email_verified ? "Verified" : "Unverified"}
          />
        </div>
      </RailSection>

      <RailSection title="Linked person">
        {person ? (
          <Link
            to="/persons/$personId"
            params={{ personId: person.id }}
            className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
          >
            <span
              aria-hidden
              className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
            >
              {personInitial(person)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-fg">
                {person.first_name} {person.last_name}
              </p>
              <p className="truncate text-[11px] text-fg/55">{person.person_type}</p>
            </div>
          </Link>
        ) : (
          <p className="text-xs text-fg/55">No person profile linked.</p>
        )}
      </RailSection>

      <RailSection title="Lifecycle">
        <LifecycleActions
          entityId={user.id}
          currentStatus={user.status}
          kind="user"
          onAction={onAction}
          loading={actionLoading}
        />
      </RailSection>
    </div>
  )
}

function DetailCard({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="rounded-sm border border-fg/10 bg-surface p-4">
      <h3 className="mb-3 text-xs font-semibold tracking-wide text-fg/55">{title}</h3>
      {children}
    </section>
  )
}

function RailSection({
  title,
  children,
  className,
}: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <section className={cn("space-y-2", className)}>
      <h3 className="text-xs font-semibold tracking-wide text-fg/55">{title}</h3>
      {children}
    </section>
  )
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-sm border border-fg/10 bg-surface px-3 py-2">
      <div className="text-[11px] font-medium tracking-wide text-fg/55">{label}</div>
      <div className="mt-0.5 font-mono text-base font-semibold text-fg">{value}</div>
    </div>
  )
}

function DetailGrid({ children }: { children: React.ReactNode }) {
  return <dl className="grid grid-cols-2 gap-x-3 gap-y-2.5">{children}</dl>
}

function DetailRow({
  label,
  value,
  fullWidth,
}: {
  label: string
  value: React.ReactNode
  fullWidth?: boolean
}) {
  return (
    <div className={cn(fullWidth && "col-span-2")}>
      <dt className="text-[11px] font-medium tracking-wide text-fg/55">{label}</dt>
      <dd className="mt-0.5 truncate text-sm text-fg">
        {value || <span className="text-fg/40">—</span>}
      </dd>
    </div>
  )
}

function personInitial(p: Person): string {
  const f = p.first_name?.[0] ?? ""
  const l = p.last_name?.[0] ?? ""
  return (f + l).toUpperCase() || "·"
}
