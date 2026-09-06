import { useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"

import { providerSpecialtiesApi } from "@/api/endpoints/provider-specialties"
import { DetailCard } from "@/components/common/DetailPrimitives"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite } from "@/hooks/useCanWrite"
import { normalizeErrorMessage } from "@/lib/errors"
import type { ProviderSpecialtyLink } from "@/types/entities"

/**
 * A practitioner's specialties, as links to the global catalogue.
 *
 * A specialty is chosen from the catalogue, not typed: a name is not proof of
 * identity. A link to a retired entry stays visible, because historical
 * records refer to it, but a retired entry cannot be newly selected.
 */
export function ProviderSpecialtiesPanel({ providerId }: { providerId: string }) {
  const toast = useToast()
  const canWrite = useCanWrite()
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState("")

  const links = useQuery({
    queryKey: ["provider-specialties", "links", providerId],
    queryFn: () => providerSpecialtiesApi.listLinks(providerId),
  })

  const catalogue = useQuery({
    queryKey: ["provider-specialties", "catalogue"],
    queryFn: () => providerSpecialtiesApi.listCatalogue(),
    staleTime: 5 * 60_000,
  })

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["provider-specialties", "links", providerId] })

  const linked = links.data ?? []
  const linkedIds = new Set(linked.map((link) => link.specialty_id))
  const available = (catalogue.data ?? []).filter((entry) => !linkedIds.has(entry.id))

  const add = async () => {
    try {
      await providerSpecialtiesApi.link(providerId, selectedId)
      await refresh()
      setSelectedId("")
      toast.showSuccess("Specialty added")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not add the specialty"))
    }
  }

  const remove = async (link: ProviderSpecialtyLink) => {
    try {
      await providerSpecialtiesApi.unlink(link.id)
      await refresh()
      toast.showSuccess("Specialty removed")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not remove the specialty"))
    }
  }

  return (
    <DetailCard title="Specialties">
      {links.isPending ? (
        <p className="text-sm text-fg-muted">Loading specialties…</p>
      ) : links.isError ? (
        <p role="alert" className="text-sm text-danger-fg">
          {normalizeErrorMessage(links.error, "Could not load specialties")}
        </p>
      ) : linked.length === 0 ? (
        <p className="text-sm text-fg-muted">No specialties recorded.</p>
      ) : (
        <ul className="flex flex-wrap gap-2">
          {linked.map((link) => (
            <li
              key={link.id}
              className="inline-flex items-center gap-1.5 border border-fg/15 bg-bg px-2 py-1"
            >
              <span className="text-sm text-fg">{link.specialty_label}</span>
              {link.specialty_is_active ? null : (
                <span className="text-[10px] font-medium tracking-wide text-fg-subtle">
                  RETIRED
                </span>
              )}
              {canWrite ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  aria-label={`Remove ${link.specialty_label}`}
                  className="size-5 p-0 text-fg/65"
                  onClick={() => void remove(link)}
                >
                  ×
                </Button>
              ) : null}
            </li>
          ))}
        </ul>
      )}

      {canWrite ? (
        <div className="mt-4 space-y-2 border-t border-fg/10 pt-4">
          <FormField
            label="Add a specialty"
            description="Chosen from the shared catalogue. Retired entries are not listed."
            htmlFor="specialty-picker"
          >
            <Select value={selectedId} onValueChange={setSelectedId}>
              <SelectTrigger id="specialty-picker">
                <SelectValue
                  placeholder={catalogue.isPending ? "Loading catalogue…" : "Choose a specialty"}
                />
              </SelectTrigger>
              <SelectContent>
                {available.map((entry) => (
                  <SelectItem key={entry.id} value={entry.id}>
                    {entry.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>
          <Button type="button" size="sm" disabled={!selectedId} onClick={() => void add()}>
            Add specialty
          </Button>
        </div>
      ) : null}
    </DetailCard>
  )
}
