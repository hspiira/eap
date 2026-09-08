import { useEffect, useState } from "react"

import { diagnosesApi } from "@/api/endpoints/diagnoses"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { normalizeErrorMessage } from "@/lib/errors"
import type { Diagnosis, DiagnosisType } from "@/types/entities"

type Target = { kind: "type" } | { kind: "diagnosis"; typeId: string }

interface DiagnosisFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  target: Target
  editing?: DiagnosisType | Diagnosis | null
  onSaved: () => void
}

export function DiagnosisFormSheet({
  open,
  onOpenChange,
  target,
  editing,
  onSaved,
}: DiagnosisFormSheetProps) {
  const isEdit = Boolean(editing)
  const [code, setCode] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [sortOrder, setSortOrder] = useState("0")
  const [submitting, setSubmitting] = useState(false)
  const [serverError, setServerError] = useState<string | undefined>(undefined)

  useEffect(() => {
    if (!open) return
    setServerError(undefined)
    setCode(editing?.code ?? "")
    setName(editing?.name ?? "")
    setDescription(editing?.description ?? "")
    setSortOrder(String(editing?.sort_order ?? 0))
  }, [open, editing])

  const label = target.kind === "type" ? "diagnosis type" : "diagnosis"

  async function save() {
    setSubmitting(true)
    setServerError(undefined)
    try {
      const common = {
        name: name.trim(),
        description: description.trim() || null,
        sort_order: Number(sortOrder) || 0,
      }
      if (target.kind === "type") {
        if (editing) await diagnosesApi.updateType(editing.id, common)
        else await diagnosesApi.createType({ ...common, code: code.trim() })
      } else {
        if (editing) await diagnosesApi.updateDiagnosis(editing.id, common)
        else
          await diagnosesApi.createDiagnosis({
            ...common,
            code: code.trim(),
            type_id: target.typeId,
          })
      }
      onSaved()
      onOpenChange(false)
    } catch (err) {
      setServerError(normalizeErrorMessage(err, `Could not save the ${label}.`))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={`${isEdit ? "Edit" : "New"} ${label}`}
      description={
        isEdit
          ? "The code is fixed once created; sessions already reference it."
          : "Shared across every tenant. Use the tenant settings to hide or relabel locally."
      }
      onSubmit={save}
      isSubmitting={submitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save" : "Create"}
    >
      <FormSection title="Identity">
        {!isEdit && (
          <FormField label="Code" required htmlFor="dx-code">
            <Input
              id="dx-code"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="WORK_STRESS_ANXIETY"
            />
          </FormField>
        )}
        <FormField label="Name" required htmlFor="dx-name">
          <Input id="dx-name" value={name} onChange={(e) => setName(e.target.value)} />
        </FormField>
        <FormField label="Description" htmlFor="dx-desc">
          <Textarea
            id="dx-desc"
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </FormField>
        <FormField label="Sort order" htmlFor="dx-sort">
          <Input
            id="dx-sort"
            type="number"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
          />
        </FormField>
      </FormSection>
    </SheetForm>
  )
}
