import { useState } from "react"

import { ChevronRight, CornerDownRight, Pencil, X } from "lucide-react"

import { IndustryFormSheet } from "@/components/IndustryFormSheet"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { Industry } from "@/types/entities"

interface IndustryDetailsCardProps {
  industry: Industry
  parent: Industry | null
  children: Industry[]
  onClose: () => void
  onUpdated: (updated: Industry) => void
  onSelectIndustry?: (id: string, hint?: Industry) => void
}

export function IndustryDetailsCard({
  industry,
  parent,
  children,
  onClose,
  onUpdated,
  onSelectIndustry,
}: IndustryDetailsCardProps) {
  const [editOpen, setEditOpen] = useState(false)

  return (
    <div className="flex min-h-0 flex-col border border-fg/10 bg-surface">
      <header className="flex items-start gap-3 border-b border-fg/10 px-4 py-3">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold leading-tight text-fg">
            {industry.name}
          </h3>
          <div className="mt-1 flex items-center gap-2">
            <span className="font-mono text-[11px] uppercase text-fg/55">
              {industry.code ?? "no code"}
            </span>
            {industry.level != null ? (
              <>
                <span className="h-3 w-px bg-fg/20" aria-hidden />
                <span className="font-mono text-[11px] text-fg/55">
                  L{industry.level}
                </span>
              </>
            ) : null}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="h-7 gap-1.5 px-2.5"
          onClick={() => setEditOpen(true)}
        >
          <Pencil className="size-3.5" />
          Edit
        </Button>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close details"
          className="grid size-7 shrink-0 place-items-center rounded-sm text-fg/55 transition-colors hover:bg-surface-hover hover:text-fg"
        >
          <X className="size-4" />
        </button>
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto p-4">
        <Section title="Hierarchy">
          {parent || children.length > 0 ? (
            <Tree
              industry={industry}
              parent={parent}
              children={children}
              onSelect={onSelectIndustry}
            />
          ) : (
            <p className="text-xs text-fg/55">Top-level industry — no parent or children.</p>
          )}
        </Section>

        <Section title="Metadata">
          <dl className="grid grid-cols-3 gap-x-3 gap-y-2.5">
            <Field label="Code" mono>
              {industry.code ?? <span className="text-fg/40">—</span>}
            </Field>
            <Field label="Level" mono>
              {industry.level != null ? `L${industry.level}` : <span className="text-fg/40">—</span>}
            </Field>
            <Field label="Children" mono>
              {children.length}
            </Field>
            <Field label="ID" mono fullWidth>
              <span className="text-fg/65">{industry.id}</span>
            </Field>
          </dl>
        </Section>
      </div>

      <IndustryFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        industry={industry}
        onSaved={onUpdated}
      />
    </div>
  )
}

function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="space-y-2">
      <h4 className="text-[11px] font-semibold uppercase tracking-wider text-fg/55">
        {title}
      </h4>
      {children}
    </section>
  )
}

function Field({
  label,
  children,
  mono,
  fullWidth,
}: {
  label: string
  children: React.ReactNode
  mono?: boolean
  fullWidth?: boolean
}) {
  return (
    <div className={cn(fullWidth && "col-span-3")}>
      <dt className="text-[10px] font-medium uppercase tracking-wider text-fg/55">
        {label}
      </dt>
      <dd className={cn("mt-0.5 truncate text-sm text-fg", mono && "font-mono text-xs")}>
        {children}
      </dd>
    </div>
  )
}

interface TreeProps {
  industry: Industry
  parent: Industry | null
  children: Industry[]
  onSelect?: (id: string, hint?: Industry) => void
}

function Tree({ industry, parent, children, onSelect }: TreeProps) {
  return (
    <ul className="space-y-1 text-sm">
      {parent ? (
        <li>
          <TreeNode industry={parent} kind="parent" onSelect={onSelect} />
        </li>
      ) : null}
      <li className={cn(parent && "ml-3 border-l border-fg/10 pl-3")}>
        <TreeNode industry={industry} kind="current" />
        {children.length > 0 ? (
          <ul className="mt-1 space-y-1">
            {children.map((c) => (
              <li key={c.id} className="ml-3 border-l border-fg/10 pl-3">
                <TreeNode industry={c} kind="child" onSelect={onSelect} />
              </li>
            ))}
          </ul>
        ) : null}
      </li>
    </ul>
  )
}

interface TreeNodeProps {
  industry: Industry
  kind: "parent" | "current" | "child"
  onSelect?: (id: string, hint?: Industry) => void
}

function TreeNode({ industry, kind, onSelect }: TreeNodeProps) {
  const Icon = kind === "parent" ? CornerDownRight : ChevronRight
  const interactive = kind !== "current" && Boolean(onSelect)
  const inner = (
    <span
      className={cn(
        "flex w-full items-center gap-1.5",
        kind === "current" && "font-medium text-primary",
        kind !== "current" && "text-fg",
      )}
    >
      <Icon
        className={cn(
          "size-3.5 shrink-0",
          kind === "current" ? "text-primary" : "text-fg/40",
        )}
      />
      <span className="truncate">{industry.name}</span>
      {industry.code ? (
        <span className="font-mono text-[11px] text-fg/55">{industry.code}</span>
      ) : null}
    </span>
  )
  if (!interactive) return inner
  return (
    <button
      type="button"
      onClick={() => onSelect?.(industry.id, industry)}
      className="-mx-1 inline-flex w-[calc(100%+0.5rem)] items-center rounded-sm px-1 py-0.5 text-left transition-colors hover:bg-surface-hover hover:[&_span:not(.font-mono)]:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      aria-label={`Open ${industry.name}`}
    >
      {inner}
    </button>
  )
}
