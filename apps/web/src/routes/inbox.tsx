import { useMemo, useState } from "react"

import { createFileRoute } from "@tanstack/react-router"
import { Link } from "@tanstack/react-router"
import { ArrowLeftRight, ArrowUpDown, BellPlus, CalendarClock, ChevronDown, ChevronLeft, ChevronRight, Eye, Filter, Heart, Infinity as InfinityIcon, Info, Monitor, Plus, Search, Share2, User, Users } from "lucide-react"

import { AppLayout } from "@/components/AppLayout"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/slices/authSlice"

export const Route = createFileRoute("/inbox")({
  component: InboxRoute,
})

type RuleStatus = "closed" | "running" | "online" | "abnormal"

interface InboxRule {
  id: string
  ruleId: string
  description: string
  serviceCallCount: number // in 万 (ten-thousands)
  status: RuleStatus
  updateTime: string
}

const STATUS_OPTIONS: { value: RuleStatus; label: string }[] = [
  { value: "closed", label: "Closed" },
  { value: "running", label: "Running" },
  { value: "online", label: "Online" },
  { value: "abnormal", label: "Abnormal" },
]

const STATUS_DOT_COLORS: Record<RuleStatus, string> = {
  closed: "bg-gray-500",
  running: "bg-blue-500",
  online: "bg-green-500",
  abnormal: "bg-red-500",
}

const STATUS_LABELS: Record<RuleStatus, string> = {
  closed: "Closed",
  running: "Running",
  online: "Online",
  abnormal: "Abnormal",
}

const MOCK_RULES: InboxRule[] = Array.from({ length: 9 }, (_, i) => ({
  id: `rule-${i}`,
  ruleId: `TradeCode ${i}`,
  description:
    i % 2 === 0
      ? "This is a description about this application and its behaviour."
      : "This is a description.",
  serviceCallCount: [9.1, 944, 9.1, 88, 9.1, 9.1, 67, 890, 312][i],
  status: (["closed", "running", "online", "abnormal"] as RuleStatus[])[i % 4],
  updateTime: `2017-10-${String(31 - (i % 3)).padStart(2, "0")} ${String(23 - (i % 12)).padStart(2, "0")}:${String((i * 7) % 60).padStart(2, "0")}:00`,
}))

const LIMIT = 9
const TOTAL_MOCK = 84

type MainTab = "training" | "courseware" | "public"
const MAIN_TABS: { id: MainTab; label: string }[] = [
  { id: "training", label: "Training list" },
  { id: "courseware", label: "My courseware" },
  { id: "public", label: "Public courseware" },
]

const DEPT_FILTERS = [
  { id: "all", label: "All", count: 34 },
  { id: "dept1", label: "Customer service", count: 10 },
  { id: "dept2", label: "CS Branch 1", count: 8 },
  { id: "dept3", label: "CS Branch 2", count: 2 },
  { id: "dept4", label: "CS Branch 3", count: 5 },
  { id: "dept5", label: "CS Branch 4", count: 9 },
]

interface PlatformDetailsRow {
  id: string
  platformName: string
  metric1: number
  change1: string
  change1Direction: "up" | "down"
  metric2: string
  change2: string
  change2Direction: "up" | "down"
  metric3: number
  outlierScore: number
  outlierMax: number
}

const MOCK_PLATFORM_DETAILS: PlatformDetailsRow[] = [
  {
    id: "meta",
    platformName: "Meta",
    metric1: 348,
    change1: "3.87%",
    change1Direction: "up",
    metric2: "9K",
    change2: "3.87%",
    change2Direction: "down",
    metric3: 309,
    outlierScore: 8,
    outlierMax: 10,
  },
]

function PlatformDetailsCard({ row }: { row: PlatformDetailsRow }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="grid grid-cols-[1fr_auto_auto_auto_auto_auto_auto_1fr] gap-3 items-center text-sm">
        <div className="font-medium text-gray-700">Platform</div>
        <div className="flex items-center justify-center w-8 text-gray-500">
          <Heart className="h-4 w-4" />
        </div>
        <div className="flex items-center justify-center w-8 text-gray-500">
          <ArrowLeftRight className="h-4 w-4" />
        </div>
        <div className="flex items-center justify-center w-8 text-gray-500">
          <Eye className="h-4 w-4" />
        </div>
        <div className="flex items-center justify-center w-8 text-gray-500">
          <ArrowLeftRight className="h-4 w-4" />
        </div>
        <div className="flex items-center justify-center w-8 text-gray-500">
          <Share2 className="h-4 w-4" />
        </div>
        <div className="col-span-2 text-right font-medium text-gray-700">Outlier Score</div>
      </div>
      <div className="mt-3 grid grid-cols-[1fr_auto_auto_auto_auto_auto_auto_1fr] gap-3 items-center">
        <div className="flex items-center gap-2">
          <InfinityIcon className="h-5 w-5 text-gray-600" />
          <span className="font-semibold text-gray-900">{row.platformName}</span>
        </div>
        <span className="font-bold text-gray-900">{row.metric1}</span>
        <span
          className={cn(
            "inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs font-medium",
            "bg-green-100 text-green-700"
          )}
        >
          {row.change1} {row.change1Direction === "up" ? "→" : "←"}
        </span>
        <span className="font-bold text-gray-900">{row.metric2}</span>
        <span
          className={cn(
            "inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs font-medium",
            "bg-green-100 text-green-700"
          )}
        >
          {row.change2Direction === "down" ? "←" : "→"} {row.change2}
        </span>
        <span className="font-bold text-gray-900">{row.metric3}</span>
        <div className="flex items-center gap-0.5">
          {Array.from({ length: row.outlierMax }).map((_, i) => (
            <div
              key={i}
              className={cn(
                "w-1.5 h-5 rounded-sm",
                i < row.outlierScore ? "bg-purple-300" : "bg-gray-200"
              )}
            />
          ))}
        </div>
        <span className="inline-flex items-center justify-end px-2 py-0.5 rounded-full text-xs font-medium bg-green-500 text-white">
          {row.outlierScore}/{row.outlierMax}
        </span>
      </div>
    </div>
  )
}

interface TrainingProgram {
  id: string
  title: string
  sessions: number
  dateFrom: string
  dateTo: string
  enrolled: number
  status: "completed" | "in_progress"
  iconVariant: "blue" | "green"
  enabled: boolean
  avatarUrls: string[]
}

const MOCK_TRAINING: TrainingProgram[] = Array.from({ length: 12 }, (_, i) => ({
  id: `training-${i}`,
  title: "New staff training",
  sessions: 10,
  dateFrom: "2021-09-12",
  dateTo: "2021-12-12",
  enrolled: 100,
  status: "completed",
  iconVariant: i === 2 || i === 6 ? "green" : "blue",
  enabled: true,
  avatarUrls: [],
}))

function TrainingCard({
  program,
  onToggle,
}: {
  program: TrainingProgram
  onToggle: (id: string) => void
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm flex flex-col min-h-45">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-md",
              program.iconVariant === "green" ? "bg-green-100 text-green-600" : "bg-blue-100 text-blue-600"
            )}
          >
            <Monitor className="h-5 w-5" />
          </div>
          <span className="font-medium text-gray-900 truncate">{program.title}</span>
        </div>
        <Switch
          checked={program.enabled}
          onCheckedChange={() => onToggle(program.id)}
          aria-label={`Toggle ${program.title}`}
        />
      </div>
      <div className="space-y-1.5 text-sm text-gray-600 mb-3">
        <span className="inline-block px-2 py-0.5 rounded bg-gray-100 text-gray-700">
          {program.sessions} sessions
        </span>
        <div className="flex items-center gap-1.5">
          <CalendarClock className="h-4 w-4 shrink-0 text-gray-400" />
          <span>
            {program.dateFrom} to {program.dateTo}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <Users className="h-4 w-4 shrink-0 text-gray-400" />
          <span>{program.enrolled} enrolled</span>
        </div>
      </div>
      <div className="mt-auto pt-3 border-t border-green-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-700">{program.status === "completed" ? "Completed" : "In progress"}</span>
            <div className="flex -space-x-2">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-6 w-6 rounded-full bg-gray-200 border-2 border-white flex items-center justify-center text-gray-500"
                >
                  <User className="h-3.5 w-3.5" />
                </div>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button type="button" variant="outline" size="sm">
              Data
            </Button>
            <Button type="button" variant="outline" size="sm">
              Details
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

function getPageNumbers(current: number, totalPages: number): (number | "ellipsis")[] {
  if (totalPages <= 9) {
    return Array.from({ length: totalPages }, (_, i) => i + 1)
  }
  const pages: (number | "ellipsis")[] = []
  if (current <= 5) {
    for (let i = 1; i <= 7; i++) pages.push(i)
    pages.push("ellipsis")
    pages.push(totalPages)
  } else if (current >= totalPages - 4) {
    pages.push(1)
    pages.push("ellipsis")
    for (let i = totalPages - 6; i <= totalPages; i++) pages.push(i)
  } else {
    pages.push(1)
    pages.push("ellipsis")
    for (let i = current - 2; i <= current + 2; i++) pages.push(i)
    pages.push("ellipsis")
    pages.push(totalPages)
  }
  return pages
}

function InboxPagination({
  page,
  total,
  limit,
  onPageChange,
}: {
  page: number
  total: number
  limit: number
  onPageChange: (page: number) => void
}) {
  const totalPages = Math.max(1, Math.ceil(total / limit))
  const pages = getPageNumbers(page, totalPages)

  return (
    <div className="flex items-center justify-end gap-1">
      <Button
        type="button"
        variant="outline"
        size="icon"
        className="size-8"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        aria-label="Previous page"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>
      {pages.map((p, i) =>
        p === "ellipsis" ? (
          <span key={`e-${i}`} className="px-2 text-gray-500">
            …
          </span>
        ) : (
          <Button
            key={p}
            type="button"
            variant={p === page ? "default" : "outline"}
            size="sm"
            className="h-8 min-w-8 px-2"
            onClick={() => onPageChange(p)}
            aria-label={`Page ${p}`}
            aria-current={p === page ? "page" : undefined}
          >
            {p}
          </Button>
        )
      )}
      <Button
        type="button"
        variant="outline"
        size="icon"
        className="size-8"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        aria-label="Next page"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  )
}

function InboxRoute() {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div
        className="min-h-svh w-full flex items-center justify-center bg-surface text-fg"
        style={{ minHeight: "100dvh" }}
      >
        <p>Loading...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-svh w-full flex flex-col items-center justify-center gap-4 bg-surface">
        <p className="text-fg">Sign in to view Inbox.</p>
        <Link to="/auth/login" search={{ tenant_code: undefined, email: undefined, redirect: undefined }} className="text-primary hover:underline">
          Sign in
        </Link>
      </div>
    )
  }

  return (
    <AppLayout>
      <InboxPage />
    </AppLayout>
  )
}

function InboxPage() {
  const [view, setView] = useState<"inbox" | "training" | "details">("inbox")
  const [mainTab, setMainTab] = useState<MainTab>("training")
  const [deptFilter, setDeptFilter] = useState("all")
  const [trainingSearch, setTrainingSearch] = useState("")
  const [ruleIdFilter, setRuleIdFilter] = useState("")
  const [statusFilter, setStatusFilter] = useState<RuleStatus | "">("")
  const [page, setPage] = useState(2)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(
    new Set(["rule-0", "rule-2", "rule-4", "rule-5"])
  )
  const [trainingEnabled, setTrainingEnabled] = useState<Record<string, boolean>>(
    Object.fromEntries(MOCK_TRAINING.map((t) => [t.id, t.enabled]))
  )

  const filteredRows = useMemo(() => {
    return MOCK_RULES.filter((r) => {
      if (ruleIdFilter && !r.ruleId.toLowerCase().includes(ruleIdFilter.toLowerCase())) return false
      if (statusFilter && r.status !== statusFilter) return false
      return true
    })
  }, [ruleIdFilter, statusFilter])

  const total = statusFilter || ruleIdFilter ? filteredRows.length : TOTAL_MOCK
  const selectedCount = selectedIds.size
  const selectedTotalCalls = MOCK_RULES.filter((r) => selectedIds.has(r.id)).reduce(
    (sum, r) => sum + r.serviceCallCount,
    0
  ) // sum in 万

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredRows.length) setSelectedIds(new Set())
    else setSelectedIds(new Set(filteredRows.map((r) => r.id)))
  }

  const clearSelection = () => setSelectedIds(new Set())

  const isAllSelected =
    filteredRows.length > 0 && selectedIds.size === filteredRows.length
  const isSomeSelected = selectedIds.size > 0
  const selectAllChecked: boolean | "indeterminate" = isAllSelected
    ? true
    : isSomeSelected
      ? "indeterminate"
      : false

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-6 border-b border-gray-200">
        {(["inbox", "training", "details"] as const).map((id) => (
          <Button
            key={id}
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setView(id)}
            className={cn(
              "h-auto rounded-none border-b-2 px-0 pb-3 -mb-px text-sm font-medium hover:bg-transparent",
              view === id
                ? "border-blue-500 text-blue-500"
                : "border-transparent text-gray-500 hover:text-gray-700"
            )}
          >
            {id === "inbox" ? "Inbox" : id === "training" ? "Training list" : "Details"}
          </Button>
        ))}
      </div>

      {view === "details" ? (
        <div className="space-y-3">
          {MOCK_PLATFORM_DETAILS.map((row) => (
            <PlatformDetailsCard key={row.id} row={row} />
          ))}
        </div>
      ) : null}

      {view === "training" ? (
        <>
          <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 pb-2">
            {MAIN_TABS.map((tab) => (
              <Button
                key={tab.id}
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setMainTab(tab.id)}
                className={cn(
                  "h-auto rounded-none border-b-2 px-1 py-2 -mb-0.5 text-sm font-medium hover:bg-transparent",
                  mainTab === tab.id
                    ? "border-blue-500 text-blue-500"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                )}
              >
                {tab.label}
              </Button>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-2 pb-2">
            {DEPT_FILTERS.map((d) => (
              <Button
                key={d.id}
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setDeptFilter(d.id)}
                className={cn(
                  "h-auto rounded-full px-3 py-1 text-sm",
                  deptFilter === d.id
                    ? "bg-blue-50 text-blue-600 font-medium hover:bg-blue-50"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                )}
              >
                {d.label} {d.count}
              </Button>
            ))}
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 pb-4">
            <div className="relative flex-1 max-w-sm">
              <Input
                placeholder="Enter search"
                value={trainingSearch}
                onChange={(e) => setTrainingSearch(e.target.value)}
                className="pl-3 pr-9 h-9 rounded-md border-gray-300 bg-white"
              />
              <Search className="absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
            </div>
            <Button
              type="button"
              className="h-9 shrink-0 bg-blue-500 px-4 text-sm font-medium text-white hover:bg-blue-600"
            >
              Add new
            </Button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {MOCK_TRAINING.map((program) => (
              <TrainingCard
                key={program.id}
                program={{ ...program, enabled: trainingEnabled[program.id] ?? program.enabled }}
                onToggle={(id) =>
                  setTrainingEnabled((prev) => ({ ...prev, [id]: !prev[id] }))
                }
              />
            ))}
          </div>
        </>
      ) : null}

      {view === "inbox" ? (
        <>
      <div className="flex flex-wrap items-end gap-3 border-b border-gray-200 pb-4">
        <div className="flex items-center gap-2">
          <Label htmlFor="rule-id" className="text-gray-700 whitespace-nowrap">
            Rule ID:
          </Label>
          <Input
            id="rule-id"
            placeholder="Enter"
            value={ruleIdFilter}
            onChange={(e) => setRuleIdFilter(e.target.value)}
            className="w-40 rounded-md border-gray-300 bg-white"
          />
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="status" className="text-gray-700 whitespace-nowrap">
            Status:
          </Label>
          <Select
            value={statusFilter || "all"}
            onValueChange={(v) => setStatusFilter(v === "all" ? "" : (v as RuleStatus))}
          >
            <SelectTrigger id="status" className="w-40 rounded-md border-gray-300 bg-white">
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent className="rounded-md border-gray-200 bg-white">
              <SelectItem value="all" className="rounded-sm">
                All
              </SelectItem>
              {STATUS_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value} className="rounded-sm">
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            className="h-9 bg-blue-500 px-4 text-sm font-medium text-white hover:bg-blue-600"
          >
            Query
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setRuleIdFilter("")
              setStatusFilter("")
            }}
            className="h-9 px-4 text-sm font-medium"
          >
            Reset
          </Button>
          <Button type="button" variant="outline" className="h-9 gap-1 px-4 text-sm font-medium">
            Expand
            <ChevronDown className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Button
            type="button"
            className="h-9 gap-1 bg-blue-500 px-4 text-sm font-medium text-white hover:bg-blue-600"
          >
            <Plus className="h-4 w-4" />
            New
          </Button>
          <Button type="button" variant="outline" className="h-9 px-4 text-sm font-medium">
            Batch operations
          </Button>
          <Button type="button" variant="outline" className="h-9 gap-1 px-4 text-sm font-medium">
            More
            <ChevronDown className="h-4 w-4" />
          </Button>
        </div>
        {selectedCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-100 rounded-md text-gray-700 text-sm">
            <Info className="h-4 w-4 shrink-0 text-blue-500" />
            <span>
              Selected {selectedCount} item{selectedCount !== 1 ? "s" : ""}. Service calls total:{" "}
              {selectedTotalCalls % 1 === 0
                ? selectedTotalCalls
                : selectedTotalCalls.toFixed(1)}{" "}
              万
            </span>
            <Button
              type="button"
              variant="link"
              size="sm"
              onClick={clearSelection}
              className="ml-1 h-auto p-0 text-blue-500"
            >
              Clear
            </Button>
          </div>
        )}
      </div>

      <div className="border border-gray-200 rounded-md overflow-hidden shadow-sm">
        <Table className="text-sm table-fixed">
          <TableHeader>
            <TableRow className="border-b border-gray-200 bg-gray-50 hover:bg-transparent">
              <TableHead className="w-9 h-8 px-2 rounded-none border-gray-200 bg-gray-50">
                <Checkbox
                  checked={selectAllChecked}
                  onCheckedChange={toggleSelectAll}
                  aria-label="Select all rows"
                />
              </TableHead>
              <TableHead className="h-8 px-2 py-1.5 rounded-none border-gray-200 bg-gray-50 text-gray-700 font-medium whitespace-nowrap w-28">
                Rule ID
              </TableHead>
              <TableHead className="h-8 px-2 py-1.5 rounded-none border-gray-200 bg-gray-50 text-gray-700 font-medium whitespace-nowrap min-w-0" style={{ width: "35%" }}>
                Description
              </TableHead>
              <TableHead className="h-8 px-2 py-1.5 rounded-none border-gray-200 bg-gray-50 text-gray-700 font-medium whitespace-nowrap w-32">
                <span className="inline-flex items-center gap-1 truncate">
                  Service call count
                  <ArrowUpDown className="h-3 w-3 shrink-0 text-gray-500" />
                </span>
              </TableHead>
              <TableHead className="h-8 px-2 py-1.5 rounded-none border-gray-200 bg-gray-50 text-gray-700 font-medium whitespace-nowrap w-24">
                <span className="inline-flex items-center gap-1">
                  Status
                  <Filter className="h-3 w-3 shrink-0 text-gray-500" />
                </span>
              </TableHead>
              <TableHead className="h-8 px-2 py-1.5 rounded-none border-gray-200 bg-gray-50 text-gray-700 font-medium whitespace-nowrap w-40">
                <span className="inline-flex items-center gap-1">
                  Update time
                  <ArrowUpDown className="h-3 w-3 shrink-0 text-gray-500" />
                </span>
              </TableHead>
              <TableHead className="h-8 px-2 py-1.5 rounded-none border-gray-200 bg-gray-50 text-gray-700 font-medium whitespace-nowrap w-20">
                Operation
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredRows.map((row, index) => (
              <TableRow
                key={row.id}
                className={cn(
                  "border-b border-gray-100",
                  index % 2 === 1 ? "bg-gray-50/60" : "bg-white"
                )}
              >
                <TableCell className="px-2 py-1.5 rounded-none w-9">
                  <Checkbox
                    checked={selectedIds.has(row.id)}
                    onCheckedChange={() => toggleSelect(row.id)}
                    aria-label={`Select rule ${row.ruleId}`}
                  />
                </TableCell>
                <TableCell className="px-2 py-1.5 rounded-none text-gray-800 overflow-hidden">
                  <span className="block truncate" title={row.ruleId}>
                    {row.ruleId}
                  </span>
                </TableCell>
                <TableCell className="px-2 py-1.5 rounded-none text-gray-700 overflow-hidden">
                  <span className="block truncate" title={row.description}>
                    {row.description}
                  </span>
                </TableCell>
                <TableCell className="px-2 py-1.5 rounded-none text-gray-700 whitespace-nowrap overflow-hidden">
                  {row.serviceCallCount % 1 === 0
                    ? row.serviceCallCount
                    : row.serviceCallCount.toFixed(1)}{" "}
                  万
                </TableCell>
                <TableCell className="px-2 py-1.5 rounded-none overflow-hidden">
                  <span className="inline-flex items-center gap-1.5 min-w-0">
                    <span
                      className={cn("h-1.5 w-1.5 rounded-full shrink-0", STATUS_DOT_COLORS[row.status])}
                    />
                    <span className="text-gray-700 truncate">{STATUS_LABELS[row.status]}</span>
                  </span>
                </TableCell>
                <TableCell className="px-2 py-1.5 rounded-none text-gray-700 overflow-hidden">
                  <span className="block truncate" title={row.updateTime}>
                    {row.updateTime}
                  </span>
                </TableCell>
                <TableCell className="px-2 py-1.5 rounded-none whitespace-nowrap">
                  <span className="flex items-center gap-1.5">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      title="Subscribe alert"
                      aria-label="Subscribe alert"
                      className="size-7 text-blue-500 hover:bg-blue-50 hover:text-blue-500"
                    >
                      <BellPlus className="h-4 w-4" />
                    </Button>
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <InboxPagination
        page={page}
        total={total}
        limit={LIMIT}
        onPageChange={setPage}
      />
        </>
      ) : null}
    </div>
  )
}
