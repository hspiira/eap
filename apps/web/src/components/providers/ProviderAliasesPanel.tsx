import { useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"

import { providerAliasesApi } from "@/api/endpoints/provider-aliases"
import { DetailCard } from "@/components/common/DetailPrimitives"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/contexts/ToastContext"
import { useCurrentRole } from "@/hooks/useCanWrite"
import { normalizeErrorMessage } from "@/lib/errors"
import { useTenantStore } from "@/store/slices/tenantSlice"
import { TenantRole } from "@/types/enums"

/** The source system session import consults. Matches SessionImportDialog. */
const ACTIVITY_LOG = "activity-log-workbook"

/**
 * The spellings an imported activity log uses for this practitioner.
 *
 * Import reads these and never writes one, so a session row spelling the name
 * any other way stalls until somebody adds it here. Adding a spelling is an
 * audited decision recorded against you, which is why it is Admin-only and why
 * a spelling already naming somebody else is refused rather than moved.
 */
export function ProviderAliasesPanel({
  providerId,
  displayName,
}: {
  providerId: string
  displayName: string
}) {
  const toast = useToast()
  const isAdmin = useCurrentRole() === TenantRole.ADMIN
  const tenantId = useTenantStore((state) => state.currentTenantId)
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState("")
  const [saving, setSaving] = useState(false)

  const aliases = useQuery({
    queryKey: ["provider-aliases", "of-provider", providerId],
    queryFn: () =>
      providerAliasesApi.list({
        tenant_id: tenantId ?? "",
        source_system: ACTIVITY_LOG,
        provider_id: providerId,
        limit: 50,
      }),
    enabled: Boolean(tenantId),
  })

  const spellings = aliases.data?.items ?? []

  const add = async () => {
    const value = draft.trim()
    if (!value || !tenantId) return
    setSaving(true)
    try {
      const { claimed } = await providerAliasesApi.adopt(tenantId, ACTIVITY_LOG, value, providerId)
      if (claimed) {
        setDraft("")
        await queryClient.invalidateQueries({ queryKey: ["provider-aliases"] })
        toast.showSuccess(`Imports spelling it ${value} now resolve to ${displayName}`)
      } else {
        toast.showError(`${value} already names another practitioner; left as it is`)
      }
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not add the spelling"))
    } finally {
      setSaving(false)
    }
  }

  return (
    <DetailCard title="Names in imports">
      {aliases.isPending ? (
        <p className="text-sm text-fg-muted">Loading spellings…</p>
      ) : aliases.isError ? (
        <p role="alert" className="text-sm text-danger-fg">
          {normalizeErrorMessage(aliases.error, "Could not load spellings")}
        </p>
      ) : spellings.length === 0 ? (
        <p className="text-sm text-fg-muted">
          No spellings recorded. Imported rows naming this practitioner will stall until one is.
        </p>
      ) : (
        <ul className="flex flex-wrap gap-2">
          {spellings.map((alias) => (
            <li
              key={alias.id}
              className="inline-flex items-center gap-1.5 border border-fg/15 bg-bg px-2 py-1"
            >
              <span className="text-sm text-fg">{alias.source_value}</span>
            </li>
          ))}
        </ul>
      )}

      {isAdmin ? (
        <div className="mt-4 space-y-2 border-t border-fg/10 pt-4">
          <FormField
            label="Add a spelling"
            description="Exactly as the activity log writes it. Case, punctuation and a leading title are ignored when matching."
            htmlFor="alias-spelling"
          >
            <div className="flex gap-2">
              <Input
                id="alias-spelling"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder={`e.g. ${displayName.toUpperCase()}`}
                className="h-8 text-xs"
              />
              <Button
                type="button"
                size="sm"
                className="h-8 shrink-0"
                disabled={saving || !draft.trim()}
                onClick={() => void add()}
              >
                {saving ? "Adding…" : "Add"}
              </Button>
            </div>
          </FormField>
        </div>
      ) : null}
    </DetailCard>
  )
}
