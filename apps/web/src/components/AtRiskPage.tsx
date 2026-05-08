import { useState } from "react"

import {
  AlertCircle,
  ArrowDown,
  ArrowUp,
  Ban,
  Check,
  ChevronLeft,
  ChevronRight,
  Circle,
  Code,
  Filter,
  MoreHorizontal,
  Plus,
  Tag,
  User,
} from "lucide-react"

import { ActivityFeedCard } from "@/components/ActivityFeedCard"
import { ApexIntroCard } from "@/components/ApexIntroCard"
import { QueryTable } from "@/components/common/QueryTable"
import { InviteToProjectCard } from "@/components/InviteToProjectCard"
import { LoggedInDevicesCard } from "@/components/LoggedInDevicesCard"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { sidebarStyles } from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"

const BREADCRUMB = "Engineering > At Risk"

const FILTER_OPTIONS = [
  { id: "status", label: "Status", icon: Circle },
  { id: "assignee", label: "Assignee", icon: User },
  { id: "label", label: "Label", icon: Tag },
  { id: "priority", label: "Priority", icon: null },
  { id: "parent", label: "Parent", icon: ArrowUp },
  { id: "sub-issue", label: "Sub-Issue", icon: ArrowDown },
  { id: "blocked", label: "Blocked issues", icon: Ban },
  { id: "blocking", label: "Blocking issues", icon: AlertCircle },
] as const

const ASSIGNEE_CHIPS = [
  { initials: "MA", bg: "bg-ink" },
  { initials: "HM", bg: "bg-danger-soft" },
  { initials: "MR", bg: "bg-natural" },
  { initials: "AO", bg: "bg-ink/80" },
]

type StatusId = "overdue" | "due-soon" | "blocked" | "needs-review"

const STATUS_COLUMNS: Array<{
  id: StatusId
  label: string
  badgeClass: string
  checkboxClass: string
  tasks: Array<{ title: string; subIssue?: number; blocked?: boolean; blocking?: boolean }>
}> = [
  {
    id: "overdue",
    label: "Overdue",
    badgeClass: "bg-danger-soft text-ink",
    checkboxClass: "border-danger-soft",
    tasks: [
      { title: "Create script for creating user accounts and onboarding flow" },
      { title: "Create Slack Integration Documentation for workspace" },
      { title: "Enable Gmail Sign-up and Sign-in functionality", blocking: true },
    ],
  },
  {
    id: "due-soon",
    label: "Due soon",
    badgeClass: "bg-natural/80 text-ink",
    checkboxClass: "border-natural",
    tasks: [
      { title: "Create backend API for sending workspace invitation" },
    ],
  },
  {
    id: "blocked",
    label: "Blocked",
    badgeClass: "bg-ink text-warm",
    checkboxClass: "border-ink",
    tasks: [
      { title: "Create backend API for sending workspace invitation" },
    ],
  },
  {
    id: "needs-review",
    label: "Needs review",
    badgeClass: "bg-natural text-warm",
    checkboxClass: "border-natural",
    tasks: [
      { title: "Create backend API for sending workspace invitation" },
    ],
  },
]

function FilterBar() {
  const [filterOpen, setFilterOpen] = useState(false)
  const [assigneeOpen, setAssigneeOpen] = useState(false)
  const [activeFilter, setActiveFilter] = useState<string | null>("Priority is any of 2 priorities")

  return (
    <div className="flex flex-nowrap items-center gap-2 border-b border-ink/20 bg-neutral-50 px-3 py-0 h-10">
      <DropdownMenu open={filterOpen} onOpenChange={setFilterOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="secondary" size="sm" className="h-8 gap-1.5 shrink-0">
            <Filter className="h-3.5 w-3.5" />
            Filter
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="min-w-[220px] p-0">
          <div className="border-b border-ink/20 p-2">
            <Input
              placeholder="Filter..."
              className="h-8 border-ink/20 bg-warm/50"
            />
          </div>
          <div className="max-h-[280px] overflow-y-auto py-1">
            {FILTER_OPTIONS.map((opt) => (
              <DropdownMenuItem
                key={opt.id}
                className="gap-2"
                onSelect={(e) => {
                  e.preventDefault()
                  if (opt.id === "assignee") setAssigneeOpen(true)
                }}
              >
                {opt.icon ? <opt.icon className="h-4 w-4" /> : <span className="w-4 h-4" />}
                {opt.label}
              </DropdownMenuItem>
            ))}
          </div>
        </DropdownMenuContent>
      </DropdownMenu>

      <div className="flex h-8 items-center gap-1.5 shrink-0">
        {ASSIGNEE_CHIPS.map((c) => (
          <span
            key={c.initials}
            className={cn(
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-medium text-warm",
              c.bg
            )}
          >
            {c.initials}
          </span>
        ))}
      </div>

      {activeFilter && (
        <div className="flex h-8 shrink-0 items-center gap-1 border border-ink/30 bg-warm px-2 py-0">
          <span className="text-sm text-ink">{activeFilter}</span>
          <button
            type="button"
            onClick={() => setActiveFilter(null)}
            className="p-0.5 text-ink hover:bg-ink/10"
            aria-label="Remove filter"
          >
            ×
          </button>
        </div>
      )}

      <DropdownMenu open={assigneeOpen} onOpenChange={setAssigneeOpen}>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            className="flex h-8 min-w-[120px] shrink-0 items-center gap-2 border border-ink/30 bg-warm px-2 py-0 text-left text-sm text-ink"
          >
            Assignee
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="min-w-[200px]">
          <DropdownMenuItem className="gap-2">
            <User className="h-4 w-4" />
            No assignee
          </DropdownMenuItem>
          <DropdownMenuItem className="gap-2">
            <span className="flex h-6 w-6 items-center justify-center bg-danger-soft text-xs text-ink">
              HM
            </span>
            HM Harshith Mullapudi
          </DropdownMenuItem>
          <DropdownMenuItem className="gap-2">
            <span className="flex h-6 w-6 items-center justify-center bg-ink/20 text-xs text-ink">
              MA
            </span>
            MA Manik Aggarwal
          </DropdownMenuItem>
          <DropdownMenuItem className="gap-2">
            <span className="flex h-6 w-6 items-center justify-center bg-natural/40 text-xs text-ink">
              MR
            </span>
            MR Manoj Reddy
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}

function TaskRow({
  title,
  subIssue,
  blocked,
  blocking,
  checkboxClass,
  isDone,
}: {
  title: string
  subIssue?: number
  blocked?: boolean
  blocking?: boolean
  checkboxClass: string
  isDone?: boolean
}) {
  return (
    <div className="flex items-center gap-2 border-b border-ink/10 py-2 last:border-b-0">
      <span
        className={cn(
          "flex h-4 w-4 shrink-0 items-center justify-center border-2 rounded-none",
          checkboxClass,
          isDone && "bg-natural border-natural"
        )}
      >
        {isDone ? <Check className="h-2.5 w-2.5 text-warm" /> : null}
      </span>
      <span className="min-w-0 flex-1 truncate text-sm text-ink">{title}</span>
      {subIssue != null && (
        <span className="shrink-0 text-xs text-ink/80">Sub-Issue {subIssue}</span>
      )}
      {blocked && (
        <span className="shrink-0 text-xs text-ink/80">Blocked by</span>
      )}
      {blocking && (
        <span className="shrink-0 border border-danger-soft bg-danger-soft/20 px-1.5 py-0.5 text-xs text-ink">
          Blocking issues
        </span>
      )}
    </div>
  )
}

export function AtRiskPage() {
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-neutral-50">
      <div
        className={cn(
          "h-10 flex items-center rounded-none bg-neutral-50",
          sidebarStyles.borderedRowBottom
        )}
      >
        <div className="flex w-full items-center gap-1.5 px-2 py-0">
          <button
            type="button"
            className="flex h-8 w-8 shrink-0 items-center justify-center py-0 text-ink hover:bg-warm"
            aria-label="Back"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            type="button"
            className="flex h-8 w-8 shrink-0 items-center justify-center py-0 text-ink hover:bg-warm"
            aria-label="Forward"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
          <Code className="h-4 w-4 shrink-0 text-ink/70" />
          <span className="min-w-0 flex-1 truncate text-sm text-ink">{BREADCRUMB}</span>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="flex h-8 w-8 shrink-0 items-center justify-center py-0 text-ink hover:bg-warm"
                aria-label="More options"
              >
                <MoreHorizontal className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>View settings</DropdownMenuItem>
              <DropdownMenuItem>Export</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <FilterBar />

      <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-4">
        <div className="mb-6">
          <QueryTable title="At Risk" />
        </div>
        <div className="mb-4 grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
          <ApexIntroCard />
          <ActivityFeedCard />
        </div>
        <div className="flex gap-4 min-w-max">
          {STATUS_COLUMNS.map((col) => (
            <div
              key={col.id}
              className="flex w-[280px] shrink-0 flex-col border border-ink/20 bg-warm/30"
            >
              <div className="flex items-center justify-between gap-2 border-b border-ink/20 px-3 py-2">
                <span
                  className={cn(
                    "inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-none",
                    col.badgeClass
                  )}
                >
                  {col.id === "needs-review" && <Check className="h-3 w-3" />}
                  {col.label}
                </span>
                <span className="text-xs text-ink">{col.tasks.length}</span>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <Plus className="h-3.5 w-3.5" />
                </Button>
              </div>
              <div className="flex flex-col p-2">
                {col.tasks.map((task, i) => (
                  <TaskRow
                    key={`${col.id}-${i}`}
                    title={task.title}
                    subIssue={task.subIssue}
                    blocked={task.blocked}
                    blocking={task.blocking}
                    checkboxClass={col.checkboxClass}
                    isDone={col.id === "needs-review" && i === col.tasks.length - 1}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-6 grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
          <InviteToProjectCard />
          <LoggedInDevicesCard />
        </div>
      </div>
    </div>
  )
}
