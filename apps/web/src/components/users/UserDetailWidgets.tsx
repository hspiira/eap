const ROLE_LABEL: Record<TenantRole, string> = {
  [TenantRole.ADMIN]: "Admin",
  [TenantRole.USER]: "User",
  [TenantRole.VIEWER]: "Viewer",
}

const SCOPE_LABEL: Record<AccessScope, string> = {
  [AccessScope.CLINICAL]: "Clinical",
  [AccessScope.EMPLOYER_PORTAL]: "Employer portal",
}

interface DetailRailProps {
  user: User
  person: Person | null
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
  onVerifyEmail: () => Promise<void>
  verifyLoading: boolean
}

import { useState } from "react"

import { Link } from "@tanstack/react-router"
import {
  BadgeCheck,
  ShieldCheck,
  UserCog,
} from "lucide-react"

import { usersApi } from "@/api/endpoints/users"
import {
  DetailCard,
  RailSection,
  Stat,
} from "@/components/common/DetailPrimitives"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/contexts/ToastContext"
import { displayName, personInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { useTenantStore } from "@/store/slices/tenantSlice"
import type { Person, User } from "@/types/entities"
import { AccessScope, TenantRole } from "@/types/enums"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export function Hero({ user }: { user: User }) {
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

export function DetailRail({ user, person, onAction, actionLoading, onVerifyEmail, verifyLoading }: DetailRailProps) {
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

export function AccessScopesCard({
  user,
  onChanged,
}: {
  user: User
  onChanged: (updated: User) => void
}) {
  const toast = useToast()
  const currentTenantId = useTenantStore((st) => st.currentTenantId)
  const platformTenant = (import.meta.env.VITE_PLATFORM_TENANT_ID ?? "").trim()
  const canGrantClinical = !platformTenant || currentTenantId === platformTenant
  const scopes = user.access_scopes ?? []
  const [submitting, setSubmitting] = useState(false)

  async function toggle(scope: AccessScope, next: boolean) {
    const updatedScopes = next ? [...scopes, scope] : scopes.filter((sc) => sc !== scope)
    setSubmitting(true)
    try {
      const updated = await usersApi.updateAccessScopes(user.id, updatedScopes)
      onChanged(updated)
      toast.showSuccess(next ? `${SCOPE_LABEL[scope]} granted` : `${SCOPE_LABEL[scope]} revoked`)
    } catch (err) {
      toast.showError(normalizeErrorMessage(err, "Could not update access scopes"))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <DetailCard title="Access scopes">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm text-fg">Clinical</p>
            <p className="text-xs text-fg/55">
              Cases, clinical notes and EAP programmes. Only platform admins can change this.
            </p>
          </div>
          <Switch
            checked={scopes.includes(AccessScope.CLINICAL)}
            disabled={submitting || !canGrantClinical}
            onCheckedChange={(v) => toggle(AccessScope.CLINICAL, v)}
          />
        </div>
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm text-fg">Employer portal</p>
            <p className="text-xs text-fg/55">Employer-facing reporting surfaces.</p>
          </div>
          <Switch
            checked={scopes.includes(AccessScope.EMPLOYER_PORTAL)}
            disabled={submitting}
            onCheckedChange={(v) => toggle(AccessScope.EMPLOYER_PORTAL, v)}
          />
        </div>
      </div>
    </DetailCard>
  )
}

export function RoleCard({
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
