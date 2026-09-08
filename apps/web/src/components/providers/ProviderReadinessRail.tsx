import { useQuery } from "@tanstack/react-query"
import { AlertCircle, CheckCircle2, CircleDashed } from "lucide-react"

import { providerSpecialtiesApi } from "@/api/endpoints/provider-specialties"
import { providersApi } from "@/api/endpoints/providers"
import { RailSection } from "@/components/common/DetailPrimitives"
import type { Provider, ProviderEligibilityFailure } from "@/types/entities"
import { AccreditationStatus, BaseStatus, PanelStatus } from "@/types/enums"

/**
 * Where each booking-gate failure is cleared. Keyed on the API's stable codes,
 * never on the message text, which is prose and may change.
 */
const FAILURE_ACTIONS: Record<string, string> = {
  provider_deleted: "This record is deleted and cannot be restored from here.",
  provider_not_active: "Set the record status to Active.",
  provider_no_profile: "Complete the practitioner profile.",
  panel_not_active: "Set the panel status to Active.",
  not_accredited: "Record accreditation.",
  accreditation_expired: "Record a current accreditation expiry.",
  organisation_not_active: "The delivering organisation is inactive.",
  organisation_not_approved: "The delivering organisation is not approved.",
  affiliation_required: "Add an affiliation for organisation delivery.",
  affiliation_not_found: "Add an affiliation for organisation delivery.",
  affiliation_not_valid_at_time: "The affiliation does not cover that date.",
  affiliation_not_permitted_for_direct: "Direct delivery cannot carry an affiliation.",
}

function CheckRow({ ok, label, detail }: { ok: boolean; label: string; detail?: string | null }) {
  const Icon = ok ? CheckCircle2 : AlertCircle
  return (
    <li className="flex items-start gap-2">
      <Icon
        aria-hidden
        className={`mt-0.5 size-3.5 shrink-0 ${ok ? "text-success-fg" : "text-danger-fg"}`}
      />
      <span className="min-w-0">
        <span className="block text-xs text-fg">{label}</span>
        {detail ? <span className="block text-[11px] text-fg-muted">{detail}</span> : null}
      </span>
    </li>
  )
}

function failureDetail(failure: ProviderEligibilityFailure): string {
  return FAILURE_ACTIONS[failure.code] ?? failure.message
}

/**
 * Whether this practitioner can take a booking, and what stands in the way.
 *
 * Two separate questions, deliberately kept apart. The booking gate is the
 * authority on eligibility and consults neither tier nor region. Profile
 * completeness is what the team still owes the record; it blocks nobody, but an
 * accredited practitioner with no tier or region is not yet usable in practice.
 */
export function ProviderReadinessRail({ provider }: { provider: Provider }) {
  const profile = provider.provider_profile
  const eligibility = useQuery({
    queryKey: ["providers", provider.id, "eligibility"],
    queryFn: () => providersApi.getEligibility(provider.id),
  })
  const specialties = useQuery({
    queryKey: ["provider-specialties", "links", provider.id],
    queryFn: () => providerSpecialtiesApi.listLinks(provider.id),
  })

  const failures = eligibility.data?.failures ?? []
  const failed = new Set(failures.map((failure) => failure.code))
  const eligible = eligibility.data?.eligible ?? false

  const gateChecks = [
    {
      code: "provider_not_active",
      label: "Record active",
      ok: provider.status === BaseStatus.ACTIVE,
    },
    {
      code: "panel_not_active",
      label: "On the active panel",
      ok: profile.panel_status === PanelStatus.ACTIVE,
    },
    {
      code: "not_accredited",
      label: "Accredited",
      ok: profile.accreditation_status === AccreditationStatus.ACCREDITED,
    },
    {
      code: "accreditation_expired",
      label: "Accreditation in date",
      ok: !failed.has("accreditation_expired"),
    },
  ]

  const specialtyCount = specialties.data?.length ?? 0
  const profileChecks = [
    { label: "Tier assessed", ok: Boolean(profile.tier) },
    { label: "Region recorded", ok: Boolean(profile.region) },
    { label: "Specialty recorded", ok: specialtyCount > 0 },
    { label: "Contact on file", ok: Boolean(provider.email || provider.phone) },
  ]
  const profileOutstanding = profileChecks.filter((check) => !check.ok).length

  return (
    <>
      <RailSection title="Booking readiness">
        {eligibility.isPending ? (
          <p className="text-xs text-fg-muted">Checking the booking gate…</p>
        ) : eligibility.isError ? (
          <p className="text-xs text-danger-fg" role="alert">
            Could not check booking eligibility.
          </p>
        ) : (
          <>
            <p
              className={`text-sm font-semibold ${eligible ? "text-success-fg" : "text-fg"}`}
              data-testid="readiness-verdict"
            >
              {eligible ? "Bookable" : "Not bookable"}
            </p>
            <ul className="space-y-1.5">
              {gateChecks.map((check) => (
                <CheckRow
                  key={check.code}
                  ok={check.ok}
                  label={check.label}
                  detail={
                    check.ok
                      ? null
                      : failureDetail(
                          failures.find((failure) => failure.code === check.code) ?? {
                            code: check.code,
                            message: "",
                          },
                        )
                  }
                />
              ))}
            </ul>
            {failures
              .filter((failure) => !gateChecks.some((check) => check.code === failure.code))
              .map((failure) => (
                <p key={failure.code} className="text-[11px] text-danger-fg">
                  {failureDetail(failure)}
                </p>
              ))}
            <p className="text-[11px] text-fg-subtle">
              A preview of the same rule the booking applies. Tier and region are not part of it.
            </p>
          </>
        )}
      </RailSection>

      <RailSection title="Profile completeness" className="border-t border-fg/10 pt-4">
        <p className="text-xs text-fg-muted">
          {profileOutstanding === 0
            ? "Nothing outstanding."
            : `${profileOutstanding} still to record. These do not block a booking.`}
        </p>
        <ul className="space-y-1.5">
          {profileChecks.map((check) => (
            <li key={check.label} className="flex items-center gap-2">
              {check.ok ? (
                <CheckCircle2 aria-hidden className="size-3.5 shrink-0 text-success-fg" />
              ) : (
                <CircleDashed aria-hidden className="size-3.5 shrink-0 text-fg-subtle" />
              )}
              <span className="text-xs text-fg">{check.label}</span>
            </li>
          ))}
        </ul>
      </RailSection>
    </>
  )
}
