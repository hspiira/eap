import { useQuery } from "@tanstack/react-query"
import { Controller } from "react-hook-form"
import { z } from "zod"

import { casesApi } from "@/api/endpoints/cases"
import { eligibleMembersApi } from "@/api/endpoints/eligible-members"
import { ClientPicker } from "@/components/common/EntityPicker"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { CaseReferralSource, PresentingProblem } from "@/types/enums"
import { CasePresentingProblemLabel,CaseReferralSourceLabel } from "@/utils/caseLabels"

const schema = z.object({
  client_id: z.string().trim().min(1, "Client is required"),
  member_id: z.string().trim().min(1, "Member is required"),
  presenting_problem: z.nativeEnum(PresentingProblem),
  referral_source: z.nativeEnum(CaseReferralSource),
  referral_notes: z.string().optional(),
})

type Values = z.infer<typeof schema>

const EMPTY: Values = {
  client_id: "",
  member_id: "",
  presenting_problem: PresentingProblem.MENTAL_HEALTH,
  referral_source: CaseReferralSource.SELF,
  referral_notes: "",
}

interface CaseFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSaved?: (result: Awaited<ReturnType<typeof casesApi.create>>) => void
}

/**
 * Opens a case. There is no edit mode — a Case's identity (client, member,
 * referral) is fixed at intake; everything else changes through lifecycle
 * actions (assign counsellor, advance, close, refer-out) on the detail page.
 */
export function CaseFormSheet({ open, onOpenChange, onSaved }: CaseFormSheetProps) {
  const { register, control, formState, submit, serverError, watch } = useEntityFormSheet<
    Values,
    Parameters<typeof casesApi.create>[0],
    Awaited<ReturnType<typeof casesApi.create>>,
    never
  >({
    resource: "cases",
    schema,
    defaultValues: EMPTY,
    open,
    onOpenChange,
    parsePayload: (values) => ({
      client_id: values.client_id,
      member_id: values.member_id,
      presenting_problem: values.presenting_problem,
      referral_source: values.referral_source,
      referral_notes: values.referral_notes?.trim() || null,
    }),
    save: ({ payload }) => casesApi.create(payload),
    successToast: { create: "Case opened" },
    onSaved,
  })

  const watchedClient = watch("client_id")
  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title="Open a case"
      description="Intake a new clinical case for an eligible member. Everything else — counsellor assignment, notes, closure — happens from the case once it's open."
      size="lg"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel="Open case"
      submittingLabel="Opening…"
    >
      <FormSection title="Who this is for">
        <FormField label="Client" required error={errors.client_id?.message}>
          <Controller
            control={control}
            name="client_id"
            render={({ field }) => <ClientPicker value={field.value} onChange={field.onChange} />}
          />
        </FormField>
        <FormField
          label="Member"
          required
          description="The eligible member roster for the selected client."
          error={errors.member_id?.message}
        >
          <Controller
            control={control}
            name="member_id"
            render={({ field }) => (
              <EligibleMemberPicker
                clientId={watchedClient}
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
        </FormField>
      </FormSection>

      <FormSection title="Referral">
        <FormField
          label="Presenting problem"
          required
          error={errors.presenting_problem?.message}
        >
          <Controller
            control={control}
            name="presenting_problem"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.values(PresentingProblem).map((p) => (
                    <SelectItem key={p} value={p}>
                      {CasePresentingProblemLabel[p]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
        <FormField label="Referral source" required error={errors.referral_source?.message}>
          <Controller
            control={control}
            name="referral_source"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.values(CaseReferralSource).map((s) => (
                    <SelectItem key={s} value={s}>
                      {CaseReferralSourceLabel[s]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
        <FormField
          label="Referral notes"
          optional
          description="Context for the counsellor picking this up — not shared with the member."
          error={errors.referral_notes?.message}
          htmlFor="case-referral-notes"
        >
          <Textarea id="case-referral-notes" rows={3} {...register("referral_notes")} />
        </FormField>
      </FormSection>
    </SheetForm>
  )
}

function EligibleMemberPicker({
  clientId,
  value,
  onChange,
}: {
  clientId: string
  value: string
  onChange: (id: string) => void
}) {
  const { data: members = [], isPending } = useQuery({
    queryKey: ["eligible-members", "for-client", clientId],
    queryFn: () => eligibleMembersApi.listForClient(clientId),
    enabled: !!clientId,
  })

  if (!clientId) {
    return (
      <Select disabled>
        <SelectTrigger>
          <SelectValue placeholder="Pick a client first" />
        </SelectTrigger>
        <SelectContent />
      </Select>
    )
  }

  return (
    <Select value={value} onValueChange={onChange} disabled={isPending}>
      <SelectTrigger>
        <SelectValue placeholder={isPending ? "Loading members…" : "Select a member"} />
      </SelectTrigger>
      <SelectContent>
        {members.map((m) => (
          <SelectItem key={m.id} value={m.id}>
            {m.display_label} · {m.employer_member_id}
          </SelectItem>
        ))}
        {!isPending && members.length === 0 ? (
          <div className="px-2 py-1.5 text-xs text-fg/55">No eligible members for this client.</div>
        ) : null}
      </SelectContent>
    </Select>
  )
}
