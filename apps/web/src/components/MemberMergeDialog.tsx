import { useEffect, useState } from "react"

import { membersApi } from "@/api/endpoints/members"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/contexts/ToastContext"
import { memberLabel } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import type { Member } from "@/types/entities"

export function MemberMergeDialog({
  open,
  onOpenChange,
  members,
  onMerged,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  members: [Member, Member] | null
  onMerged: () => void
}) {
  const toast = useToast()
  const [targetId, setTargetId] = useState("")
  const [loading, setLoading] = useState(false)
  useEffect(() => setTargetId(members?.[0].id ?? ""), [members])
  if (!members) return null
  const source = members.find((member) => member.id !== targetId)
  const target = members.find((member) => member.id === targetId)

  const merge = async () => {
    if (!target || !source) return
    setLoading(true)
    try {
      const result = await membersApi.merge(target.id, source.id)
      toast.showSuccess(`${memberLabel(source)} merged into ${memberLabel(result.member)}`)
      onMerged()
      onOpenChange(false)
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not merge these members"))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-none">
        <DialogHeader>
          <DialogTitle>Merge duplicate members</DialogTitle>
          <DialogDescription>
            Choose the member to keep. Sessions, beneficiaries, contacts, account linkage and
            clinical continuity move to that record. The other member is permanently removed.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="merge-survivor">Member to keep</Label>
          <Select value={targetId} onValueChange={setTargetId}>
            <SelectTrigger id="merge-survivor" className="rounded-none">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="rounded-none">
              {members.map((member) => (
                <SelectItem key={member.id} value={member.id}>
                  {memberLabel(member)} · {member.employer_member_id}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {source ? (
            <p className="text-xs text-danger-fg">
              Will remove {memberLabel(source)} ({source.employer_member_id}).
            </p>
          ) : null}
        </div>
        <DialogFooter>
          <Button variant="outline" disabled={loading} onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button variant="destructive" disabled={loading || !source} onClick={() => void merge()}>
            {loading ? "Merging…" : "Merge members"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
