import { useEffect,useState } from "react"

import { Building2,ChevronRight, Pencil, X } from "lucide-react"

import { industriesApi } from "@/api/endpoints/industries"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import type { Industry } from "@/types/entities"

type IndustryDetailsCardProps = {
  industry: Industry
  parent: Industry | null
  children: Industry[]
  onClose: () => void
  onUpdated: (updated: Industry) => void
}

export function IndustryDetailsCard({
  industry,
  parent,
  children,
  onClose,
  onUpdated,
}: IndustryDetailsCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [name, setName] = useState(industry.name)
  const [code, setCode] = useState(industry.code ?? "")
  const [level, setLevel] = useState(industry.level != null ? String(industry.level) : "")

  useEffect(() => {
    setName(industry.name)
    setCode(industry.code ?? "")
    setLevel(industry.level != null ? String(industry.level) : "")
  }, [industry.id, industry.name, industry.code, industry.level])

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await industriesApi.update(industry.id, {
        name: name.trim() || industry.name,
        code: code.trim() || null,
        level: level.trim() ? parseInt(level, 10) : null,
      })
      onUpdated(updated)
      setIsEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setName(industry.name)
    setCode(industry.code ?? "")
    setLevel(industry.level != null ? String(industry.level) : "")
    setIsEditing(false)
  }

  return (
    <div className="border border-[#bfc4c9]/25 bg-white p-4 flex flex-col min-h-0">
      <div className="mb-3 flex items-center justify-between shrink-0">
        <h3 className="text-sm font-semibold text-[#5A626A] truncate min-w-0">
          {industry.name || "Industry"}
        </h3>
        <button
          type="button"
          className="p-1 text-[#5A626A]/70 hover:text-[#5A626A] shrink-0"
          aria-label="Close"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-3 flex-1 min-h-0 overflow-y-auto">
        {isEditing ? (
          <div className="space-y-2">
            <div>
              <label className="text-xs font-medium text-[#5A626A]/80 block mb-1">Name</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-8 text-sm rounded-none"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-[#5A626A]/80 block mb-1">Code</label>
              <Input
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="h-8 text-sm rounded-none"
                placeholder="Optional"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-[#5A626A]/80 block mb-1">Level</label>
              <Input
                type="number"
                min={0}
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                className="h-8 text-sm rounded-none"
                placeholder="Optional"
              />
            </div>
            <div className="flex gap-2 pt-1">
              <Button size="sm" onClick={handleSave} disabled={saving} className="rounded-none">
                {saving ? "Saving…" : "Save"}
              </Button>
              <Button size="sm" variant="secondary" onClick={handleCancel} className="rounded-none">
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <dl className="grid gap-1.5 text-sm">
              <div>
                <dt className="text-[#5A626A]/70">Name</dt>
                <dd className="text-[#5A626A] font-medium">{industry.name}</dd>
              </div>
              <div>
                <dt className="text-[#5A626A]/70">Code</dt>
                <dd className="text-[#5A626A]">{industry.code ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-[#5A626A]/70">Level</dt>
                <dd className="text-[#5A626A]">{industry.level != null ? industry.level : "—"}</dd>
              </div>
            </dl>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => setIsEditing(true)}
              className="rounded-none gap-1.5"
            >
              <Pencil className="h-3.5 w-3.5" />
              Edit
            </Button>
          </div>
        )}

        <div className="border-t border-[#bfc4c9]/25 pt-3">
          <h4 className="text-xs font-semibold text-[#5A626A] mb-2">Hierarchy</h4>
          <ul className="space-y-1.5">
            {parent && (
              <li className="flex items-center gap-2 text-sm">
                <Building2 className="h-3.5 w-3.5 text-[#5A626A]/60 shrink-0" />
                <span className="text-[#5A626A]/80">Parent: {parent.name}</span>
                {parent.code && (
                  <span className="text-[#5A626A]/50 text-xs">({parent.code})</span>
                )}
              </li>
            )}
            <li className="flex items-center gap-2 text-sm">
              <ChevronRight className="h-3.5 w-3.5 text-natural shrink-0" />
              <span className="text-[#5A626A] font-medium">{industry.name}</span>
              {industry.code && (
                <span className="text-[#5A626A]/50 text-xs">({industry.code})</span>
              )}
            </li>
            {children.length > 0 &&
              children.map((child) => (
                <li key={child.id} className="flex items-center gap-2 pl-4 text-sm">
                  <Building2 className="h-3.5 w-3.5 text-[#5A626A]/60 shrink-0" />
                  <span className="text-[#5A626A]/90">{child.name}</span>
                  {child.code && (
                    <span className="text-[#5A626A]/50 text-xs">({child.code})</span>
                  )}
                </li>
              ))}
            {!parent && children.length === 0 && (
              <li className="text-xs text-[#5A626A]/60">No parent or children</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  )
}
