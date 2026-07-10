import { useCallback, useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  CalendarClock,
  CalendarRange,
  Pencil,
  RotateCw,
  Star,
  Users,
  Wrench,
} from "lucide-react"

import { personsApi } from "@/api/endpoints/persons"
import { providersApi } from "@/api/endpoints/providers"
import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { EmptyState } from "@/components/common/EmptyState"
import { FormField } from "@/components/common/FormField"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { ServiceSessionFormSheet } from "@/components/ServiceSessionFormSheet"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { cn } from "@/lib/utils"
import type {
  Person,
  Provider,
  Service,
  ServiceSession,
} from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/service-sessions/$sessionId")({
  component: ServiceSessionDetailPage,
})

type TabValue = "overview" | "feedback" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "feedback", "history"]

function ServiceSessionDetailPage() {
  const { sessionId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()
  const [session, setSession] = useState<ServiceSession | null>(null)
  const [service, setService] = useState<Service | null>(null)
  const [person, setPerson] = useState<Person | null>(null)
  const [provider, setProvider] = useState<Provider | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [editOpen, setEditOpen] = useState(false)
  const [rescheduleOpen, setRescheduleOpen] = useState(false)

  const fetchSession = useCallback(async () => {
    try {
      setLoading(true)
      setSession(await serviceSessionsApi.getById(sessionId))
    } catch (_err) {
      setSession(null)
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    fetchSession()
  }, [fetchSession])

  useEffect(() => {
    if (!session) {
      setService(null)
      setPerson(null)
      setProvider(null)
      return
    }
    let cancelled = false
    servicesApi
      .getById(session.service_id)
      .then((s) => {
        if (!cancelled) setService(s)
      })
      .catch(() => {
        if (!cancelled) setService(null)
      })
    personsApi
      .getById(session.person_id)
      .then((p) => {
        if (!cancelled) setPerson(p)
      })
      .catch(() => {
        if (!cancelled) setPerson(null)
      })
    if (session.service_provider_id) {
      providersApi
        .list({ page: 1, limit: 1, search: session.service_provider_id })
        .then((res) => {
          if (cancelled) return
          const found = (res.items ?? []).find(
            (p) => p.id === session.service_provider_id,
          )
          setProvider(found ?? null)
        })
        .catch(() => {
          if (!cancelled) setProvider(null)
        })
    } else {
      setProvider(null)
    }
    return () => {
      cancelled = true
    }
  }, [session])

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      setActionLoading(true)
      try {
        // BE requires a body on complete/cancel; minimal sane defaults for now.
        // TODO(P1): surface a dialog to capture duration+notes / cancel reason.
        if (action === "complete") {
          await serviceSessionsApi.complete(id, {
            duration: 60,
            notes: "Session completed.",
          })
        } else if (action === "cancel") {
          await serviceSessionsApi.cancel(id, { reason: "Cancelled by counsellor." })
        } else if (action === "no-show") await serviceSessionsApi.noShow(id)
        else if (action === "archive") await serviceSessionsApi.archive(id)
        else if (action === "restore") await serviceSessionsApi.restore(id)
        else if (action === "reschedule") setRescheduleOpen(true)
        await fetchSession()
        await queryClient.invalidateQueries({ queryKey: ["service-sessions", "list"] })
      } finally {
        setActionLoading(false)
      }
    },
    [fetchSession, queryClient],
  )

  const submitFeedback = useCallback(
    async (rating: number | null, comments: string | null) => {
      if (!session) return
      try {
        // BE accepts `{feedback: string≥1}` only — combine rating + comments
        // into a single line until we surface a richer feedback shape on the BE.
        const feedbackText = [
          rating != null ? `Rating: ${rating}/5` : null,
          comments?.trim() || null,
        ]
          .filter(Boolean)
          .join(" — ")
        if (!feedbackText) {
          showError("Add a rating or comment before saving.")
          return
        }
        const updated = await serviceSessionsApi.updateFeedback(session.id, {
          feedback: feedbackText,
        })
        setSession(updated)
        showSuccess("Feedback saved")
      } catch (err) {
        showError(err instanceof Error ? err.message : "Failed to save feedback")
      }
    },
    [session, showSuccess, showError],
  )

  if (loading) {
    return (
      <PageShell icon={CalendarClock} breadcrumb="Delivery · Sessions · …">
        <div className="min-h-0 flex-1 overflow-auto p-5">
          <DetailSkeleton />
        </div>
      </PageShell>
    )
  }

  if (!session) {
    return (
      <PageShell icon={CalendarClock} breadcrumb="Delivery · Sessions · Not found">
        <EmptyState
          icon={CalendarClock}
          title="Session not found"
          description="It may have been archived or never existed."
          action={
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => navigate({ to: "/service-sessions" })}
            >
              <ArrowLeft className="size-4" />
              Back to sessions
            </Button>
          }
        />
      </PageShell>
    )
  }

  return (
    <PageShell
      icon={CalendarClock}
      breadcrumb={`Delivery · Sessions · ${new Date(session.scheduled_at).toLocaleString()}`}
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/service-sessions" })}
            aria-label="Back to sessions"
            title="Back to sessions"
            className="size-7 p-0 text-fg/70"
          >
            <ArrowLeft className="size-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={fetchSession}
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
      <Hero session={session} service={service} person={person} />

      <ServiceSessionFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        session={session}
        service={service}
        person={person}
        onSaved={(updated) => setSession(updated)}
      />

      <RescheduleDialog
        open={rescheduleOpen}
        onOpenChange={setRescheduleOpen}
        currentISO={session.scheduled_at}
        onConfirm={async (iso, notes) => {
          // BE `ServiceSessionRescheduleRequest` only carries the new datetime.
          // If reschedule notes are useful, we'd PATCH them via update() after.
          const updated = await serviceSessionsApi.reschedule(session.id, {
            new_scheduled_at: iso,
          })
          if (notes?.trim()) {
            await serviceSessionsApi.update(session.id, { notes: notes.trim() })
          }
          setSession(updated)
          await queryClient.invalidateQueries({
            queryKey: ["service-sessions", "list"],
          })
          showSuccess("Session rescheduled")
        }}
      />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="feedback">Feedback</Tab>
                <Tab value="history">History</Tab>
              </TabsList>

              <TabPanel value="overview">
                <BackfillNotice session={session} />
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Schedule">
                    <DetailGrid>
                      <DetailRow
                        label="Scheduled at"
                        value={new Date(session.scheduled_at).toLocaleString()}
                        fullWidth
                      />
                      <DetailRow
                        label="Completed at"
                        value={
                          session.completed_at
                            ? new Date(session.completed_at).toLocaleString()
                            : null
                        }
                        fullWidth
                      />
                      <DetailRow label="Status" value={<StatusBadge status={session.status} />} />
                      <DetailRow label="Location" value={session.location} />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Notes">
                    {session.notes ? (
                      <p className="text-sm text-fg whitespace-pre-wrap">{session.notes}</p>
                    ) : (
                      <p className="text-xs text-fg/55">No notes recorded.</p>
                    )}
                  </DetailCard>

                  <DetailCard title="Subject">
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
                      <p className="text-xs text-fg/55">Loading person…</p>
                    )}
                  </DetailCard>

                  <DetailCard title="Service & provider">
                    {service ? (
                      <Link
                        to="/services/$serviceId"
                        params={{ serviceId: service.id }}
                        className="mb-2 flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2 transition-colors hover:border-fg/25"
                      >
                        <span
                          aria-hidden
                          className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
                        >
                          <Wrench className="size-3.5" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-fg">
                            {service.name}
                          </p>
                          <p className="truncate text-[11px] text-fg/55">
                            {service.service_type ?? "—"}
                          </p>
                        </div>
                      </Link>
                    ) : null}
                    {provider ? (
                      <div className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2">
                        <span
                          aria-hidden
                          className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
                        >
                          PR
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-mono text-sm font-medium text-fg">
                            {provider.id}
                          </p>
                          <p className="truncate text-[11px] text-fg/55">
                            {provider.provider_profile.tier} ·{" "}
                            {provider.provider_profile.region}
                          </p>
                        </div>
                      </div>
                    ) : session.service_provider_id ? (
                      <p className="text-xs text-fg/55">Loading provider…</p>
                    ) : (
                      <p className="text-xs text-fg/55">No provider assigned.</p>
                    )}
                  </DetailCard>

                  <DetailCard title="Clinical">
                    <DetailGrid>
                      <DetailRow
                        label="Diagnosis ID"
                        value={
                          session.diagnosis_id ? (
                            <span className="font-mono text-xs">
                              {session.diagnosis_id}
                            </span>
                          ) : null
                        }
                        fullWidth
                      />
                      {session.diagnosis_text ? (
                        <DetailRow
                          label="Diagnosis (free text)"
                          value={session.diagnosis_text}
                          fullWidth
                        />
                      ) : null}
                    </DetailGrid>
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="feedback">
                <FeedbackPanel session={session} onSubmit={submitFeedback} />
              </TabPanel>

              <TabPanel value="history">
                <EmptyState
                  title="No activity yet"
                  description="Reschedule and lifecycle events will appear here once the audit feed is wired up."
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              session={session}
              service={service}
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

function Hero({
  session,
  service,
  person,
}: {
  session: ServiceSession
  service: Service | null
  person: Person | null
}) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <CalendarClock className="size-4" />
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {new Date(session.scheduled_at).toLocaleString()}
      </h1>
      {service ? (
        <Link
          to="/services/$serviceId"
          params={{ serviceId: service.id }}
          className="text-xs text-fg/65 hover:text-primary"
        >
          {service.name}
        </Link>
      ) : null}
      {person ? (
        <Link
          to="/persons/$personId"
          params={{ personId: person.id }}
          className="text-xs text-fg/65 hover:text-primary"
        >
          · {person.first_name} {person.last_name}
        </Link>
      ) : null}
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <StatusBadge status={session.status} />
    </div>
  )
}

interface DetailRailProps {
  session: ServiceSession
  service: Service | null
  person: Person | null
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
}

function DetailRail({
  session,
  service,
  person,
  onAction,
  actionLoading,
}: DetailRailProps) {
  const rating = session.feedback?.rating ?? null
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <div className="grid grid-cols-2 gap-3">
          <Stat
            label="Duration"
            value={service?.duration_minutes != null ? `${service.duration_minutes}m` : "—"}
          />
          <Stat
            label="Rating"
            value={rating != null ? `${rating}/5` : "—"}
          />
        </div>
      </RailSection>

      <RailSection title="Linked">
        <div className="space-y-2">
          {service ? (
            <Link
              to="/services/$serviceId"
              params={{ serviceId: service.id }}
              className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
            >
              <span
                aria-hidden
                className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
              >
                <Wrench className="size-3.5" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-fg">{service.name}</p>
                <p className="truncate text-[11px] text-fg/55">
                  {service.service_type ?? "—"}
                </p>
              </div>
            </Link>
          ) : null}
          {person ? (
            <Link
              to="/persons/$personId"
              params={{ personId: person.id }}
              className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
            >
              <span
                aria-hidden
                className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
              >
                <Users className="size-3.5" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-fg">
                  {person.first_name} {person.last_name}
                </p>
                <p className="truncate text-[11px] text-fg/55">{person.person_type}</p>
              </div>
            </Link>
          ) : null}
        </div>
      </RailSection>

      <RailSection title="Lifecycle">
        <LifecycleActions
          entityId={session.id}
          currentStatus={session.status}
          kind="session"
          onAction={onAction}
          loading={actionLoading}
        />
      </RailSection>
    </div>
  )
}

function FeedbackPanel({
  session,
  onSubmit,
}: {
  session: ServiceSession
  onSubmit: (rating: number | null, comments: string | null) => Promise<void>
}) {
  const [rating, setRating] = useState<number | null>(session.feedback?.rating ?? null)
  const [comments, setComments] = useState(session.feedback?.comments ?? "")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setRating(session.feedback?.rating ?? null)
    setComments(session.feedback?.comments ?? "")
  }, [session])

  const submit = async () => {
    setSaving(true)
    try {
      await onSubmit(rating, comments.trim() || null)
    } finally {
      setSaving(false)
    }
  }

  return (
    <DetailCard title="Subject feedback">
      <div className="space-y-4">
        <FormField label="Rating" optional>
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((n) => (
              <Button
                key={n}
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setRating(rating === n ? null : n)}
                aria-label={`${n} stars`}
                className={cn(
                  "size-8 p-0 hover:bg-surface-hover",
                  rating != null && n <= rating ? "text-primary" : "text-fg/35",
                )}
              >
                <Star
                  className={cn(
                    "size-4",
                    rating != null && n <= rating ? "fill-primary" : "",
                  )}
                />
              </Button>
            ))}
            {rating != null ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setRating(null)}
                className="ml-2 h-auto p-0 text-xs text-fg/55 hover:bg-transparent hover:text-fg"
              >
                Clear
              </Button>
            ) : null}
          </div>
        </FormField>
        <FormField label="Comments" optional htmlFor="ss-comments">
          <Input
            id="ss-comments"
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            placeholder="Anything the subject shared about the session…"
          />
        </FormField>
        <div className="flex justify-end">
          <Button size="sm" onClick={submit} disabled={saving}>
            {saving ? "Saving…" : "Save feedback"}
          </Button>
        </div>
      </div>
    </DetailCard>
  )
}

function RescheduleDialog({
  open,
  onOpenChange,
  currentISO,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  currentISO: string
  onConfirm: (iso: string, notes: string) => Promise<void>
}) {
  const [scheduled, setScheduled] = useState(toLocalDatetime(currentISO))
  const [notes, setNotes] = useState("")
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (open) {
      setScheduled(toLocalDatetime(currentISO))
      setNotes("")
    }
  }, [open, currentISO])

  const handleConfirm = async () => {
    if (!scheduled) return
    setSubmitting(true)
    try {
      await onConfirm(new Date(scheduled).toISOString(), notes)
      onOpenChange(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Reschedule session</DialogTitle>
          <DialogDescription>
            <CalendarRange className="mr-1 inline size-3" />
            Previous time: {new Date(currentISO).toLocaleString()}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <FormField label="New scheduled time" required htmlFor="reschedule-when">
            <Input
              id="reschedule-when"
              type="datetime-local"
              value={scheduled}
              onChange={(e) => setScheduled(e.target.value)}
            />
          </FormField>
          <FormField label="Reason / notes" optional htmlFor="reschedule-notes">
            <Input
              id="reschedule-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Why is this being rescheduled?"
            />
          </FormField>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={handleConfirm}
            disabled={!scheduled || submitting}
          >
            {submitting ? "Saving…" : "Reschedule"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
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

function toLocalDatetime(iso: string): string {
  if (!iso) return ""
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ""
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function BackfillNotice({ session }: { session: ServiceSession }) {
  const backfill = (session.metadata as Record<string, unknown> | null | undefined)
    ?.backfill as
    | { logged_at?: string; reason?: string | null; source?: string }
    | undefined
  if (!backfill) return null
  return (
    <div className="mb-4 rounded-sm border border-fg/15 bg-surface px-3 py-2.5">
      <div className="flex items-start gap-2.5">
        <CalendarRange className="mt-0.5 size-3.5 shrink-0 text-fg/65" />
        <div className="min-w-0 flex-1 text-xs">
          <p className="font-medium text-fg">Logged after the fact</p>
          <p className="mt-0.5 text-fg/65">
            Entered{" "}
            {backfill.logged_at
              ? new Date(backfill.logged_at).toLocaleString()
              : "later"}
            {backfill.reason ? ` · ${backfill.reason}` : null}
          </p>
        </div>
      </div>
    </div>
  )
}

