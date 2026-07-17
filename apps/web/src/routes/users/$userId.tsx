import { useCallback, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  BadgeCheck,
  KeyRound,
  Pencil,
  ShieldCheck,
  ShieldOff,
  UserCog,
} from "lucide-react"

import { personsApi } from "@/api/endpoints/persons"
import { usersApi } from "@/api/endpoints/users"
import { renderDetailState } from "@/components/common/DetailStates"
import { EmptyState } from "@/components/common/EmptyState"
import { FormField } from "@/components/common/FormField"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { PageShell } from "@/components/common/PageShell"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { UserFormSheet } from "@/components/UserFormSheet"
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite } from "@/hooks/useCanWrite"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { displayName, personInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey, useEntityDetail } from "@/lib/queries"
import { cn } from "@/lib/utils"
import type { Person, User } from "@/types/entities"
import { AuthProvider, TenantRole } from "@/types/enums"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/users/$userId")({
  component: UserDetailPage,
})

type TabValue = "overview" | "security" | "preferences" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "security", "preferences", "history"]

function UserDetailPage() {
  const { userId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [actionLoading, setActionLoading] = useState(false)
  const toast = useToast()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [editOpen, setEditOpen] = useState(false)
  const [verifyLoading, setVerifyLoading] = useState(false)
  const canWrite = useCanWrite()

  const userQuery = useEntityDetail<User>({
    resource: "users",
    id: userId,
    detailFn: usersApi.getById,
  })
  const user = userQuery.data ?? null

  const { data: person = null } = useQuery({
    queryKey: ["persons", "by-user", userId],
    queryFn: () => personsApi.getByUserId(userId),
    enabled: !!user,
  })

  const [reasonPrompt, setReasonPrompt] = useState<{
    action: "suspend" | "ban" | "terminate" | "deactivate"
    id: string
  } | null>(null)
  const [reasonValue, setReasonValue] = useState("")

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      if (action === "suspend" || action === "ban" || action === "terminate" || action === "deactivate") {
        setReasonPrompt({ action, id })
        setReasonValue("")
        return
      }
      setActionLoading(true)
      try {
        if (action === "activate") await usersApi.activate(id)
        await queryClient.invalidateQueries({ queryKey: ["users"] })
        toast.showSuccess("Status updated")
      } catch (err) {
        toast.showError(normalizeErrorMessage(err, "Action failed — please try again"))
      } finally {
        setActionLoading(false)
      }
    },
    [queryClient, toast],
  )

  const handleVerifyEmail = useCallback(async () => {
    setVerifyLoading(true)
    try {
      await usersApi.verifyEmail(userId)
      await queryClient.invalidateQueries({ queryKey: ["users"] })
      toast.showSuccess("Email marked as verified")
    } catch (err) {
      toast.showError(normalizeErrorMessage(err, "Could not verify email — please try again"))
    } finally {
      setVerifyLoading(false)
    }
  }, [queryClient, toast, userId])

  const confirmReasonAction = useCallback(async () => {
    if (!reasonPrompt) return
    const reason = reasonValue.trim()
    if (!reason && reasonPrompt.action !== "deactivate") return
    setActionLoading(true)
    try {
      const { action, id } = reasonPrompt
      if (action === "suspend") await usersApi.suspend(id, reason)
      else if (action === "ban") await usersApi.ban(id, reason)
      else if (action === "terminate") await usersApi.terminate(id, reason)
      else if (action === "deactivate")
        await usersApi.deactivate(id, reason || undefined)
      await queryClient.invalidateQueries({ queryKey: ["users"] })
      setReasonPrompt(null)
      setReasonValue("")
      toast.showSuccess("Status updated")
    } catch (err) {
      toast.showError(normalizeErrorMessage(err, "Action failed — please try again"))
    } finally {
      setActionLoading(false)
    }
  }, [queryClient, reasonPrompt, reasonValue, toast])

  const state = renderDetailState(userQuery, {
    icon: UserCog,
    breadcrumb: "People · Platform Users",
    entity: "user",
    backTo: () => navigate({ to: "/users" }),
    backLabel: "Back to users",
  })
  if (state || !user) return state

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
          {canWrite && (
            <Button
              size="sm"
              variant="outline"
              className="h-7 gap-1.5 px-2.5"
              onClick={() => setEditOpen(true)}
            >
              <Pencil className="size-3.5" />
              Edit
            </Button>
          )}
        </>
      }
    >
      <Hero user={user} />

      <UserFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        user={user}
        onSaved={(updated) =>
          queryClient.setQueryData(entityDetailKey("users", updated.id), updated)
        }
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
                          {personInitials(person, user)}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-fg">
                            {displayName(person, user)}
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

                  <div className="mt-4">
                    <RoleCard
                      user={user}
                      onChanged={(updated) =>
                        queryClient.setQueryData(
                          entityDetailKey("users", updated.id),
                          updated,
                        )
                      }
                    />
                  </div>
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

                <div className="mt-4">
                  <DetailCard title="Sign-in method">
                    <DetailGrid>
                      <DetailRow
                        label="Provider"
                        value={
                          user.auth_provider === AuthProvider.AZURE_AD ? (
                            <span className="inline-flex items-center gap-1 text-fg">
                              <KeyRound className="size-3.5 text-primary" /> Microsoft (Azure AD)
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-fg/75">
                              <KeyRound className="size-3.5" /> Tenant password
                            </span>
                          )
                        }
                      />
                      <DetailRow
                        label="Azure OID"
                        value={
                          user.azure_oid ? (
                            <span className="font-mono text-xs">{user.azure_oid}</span>
                          ) : (
                            <span className="text-fg/55">Not linked</span>
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
              onVerifyEmail={handleVerifyEmail}
              verifyLoading={verifyLoading}
            />
          </aside>
        </div>
      </div>

      <Dialog
        open={reasonPrompt !== null}
        onOpenChange={(o) => {
          if (!o) {
            setReasonPrompt(null)
            setReasonValue("")
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {reasonPrompt?.action === "ban"
                ? "Ban user"
                : reasonPrompt?.action === "terminate"
                  ? "Terminate user"
                  : reasonPrompt?.action === "deactivate"
                    ? "Deactivate user"
                    : "Suspend user"}
            </DialogTitle>
            <DialogDescription>
              {reasonPrompt?.action === "terminate"
                ? "Termination is permanent. The user cannot be reactivated afterwards."
                : reasonPrompt?.action === "ban"
                  ? "The user will be banned from signing in. Audit trail captures this reason."
                  : reasonPrompt?.action === "deactivate"
                    ? "The user will be deactivated. A reason is optional."
                    : "The user cannot sign in while suspended. Reason is required and logged."}
            </DialogDescription>
          </DialogHeader>
          <FormField
            label="Reason"
            htmlFor="user-action-reason"
            required={reasonPrompt?.action !== "deactivate"}
          >
            <Input
              id="user-action-reason"
              placeholder="e.g. role transferred"
              value={reasonValue}
              onChange={(e) => setReasonValue(e.target.value)}
              autoFocus
            />
          </FormField>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setReasonPrompt(null)
                setReasonValue("")
              }}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={confirmReasonAction}
              disabled={
                actionLoading ||
                (reasonPrompt?.action !== "deactivate" && !reasonValue.trim())
              }
            >
              {actionLoading ? "Submitting…" : "Confirm"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
  onVerifyEmail: () => Promise<void>
  verifyLoading: boolean
}

function DetailRail({ user, person, onAction, actionLoading, onVerifyEmail, verifyLoading }: DetailRailProps) {
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
              {personInitials(person)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-fg">
                {displayName(person, user)}
              </p>
              <p className="truncate text-[11px] text-fg/55">{person.person_type}</p>
            </div>
          </Link>
        ) : (
          <p className="text-xs text-fg/55">No person profile linked.</p>
        )}
      </RailSection>

      {!user.is_email_verified && (
        <RailSection title="Account">
          <Button
            variant="outline"
            size="sm"
            className="w-full gap-1.5"
            onClick={onVerifyEmail}
            disabled={verifyLoading}
          >
            <BadgeCheck className="size-3.5" />
            {verifyLoading ? "Verifying…" : "Mark email as verified"}
          </Button>
        </RailSection>
      )}

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

const ROLE_LABEL: Record<TenantRole, string> = {
  [TenantRole.ADMIN]: "Admin",
  [TenantRole.USER]: "User",
  [TenantRole.VIEWER]: "Viewer",
}

function RoleCard({
  user,
  onChanged,
}: {
  user: User
  onChanged: (updated: User) => void
}) {
  const toast = useToast()
  const currentRole = (user.role ?? TenantRole.USER) as TenantRole
  const [editing, setEditing] = useState(false)
  const [nextRole, setNextRole] = useState<TenantRole>(currentRole)
  const [submitting, setSubmitting] = useState(false)

  async function save() {
    if (nextRole === currentRole) {
      setEditing(false)
      return
    }
    setSubmitting(true)
    try {
      const updated = await usersApi.updateRole(user.id, { role: nextRole })
      onChanged(updated)
      toast.showSuccess(`Role changed to ${ROLE_LABEL[nextRole]}`)
      setEditing(false)
    } catch (err) {
      toast.showError(normalizeErrorMessage(err, "Could not change role"))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <DetailCard title="Tenant role">
      {editing ? (
        <div className="space-y-3">
          <Select value={nextRole} onValueChange={(v) => setNextRole(v as TenantRole)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[TenantRole.ADMIN, TenantRole.USER, TenantRole.VIEWER].map((r) => (
                <SelectItem key={r} value={r}>
                  {ROLE_LABEL[r]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="flex gap-2">
            <Button type="button" size="sm" onClick={save} disabled={submitting}>
              {submitting ? "Saving…" : "Save"}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                setNextRole(currentRole)
                setEditing(false)
              }}
              disabled={submitting}
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm text-fg">{ROLE_LABEL[currentRole]}</span>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => {
              setNextRole(currentRole)
              setEditing(true)
            }}
          >
            Change
          </Button>
        </div>
      )}
    </DetailCard>
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

