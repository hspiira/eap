import { useState } from "react"
import { Search, RotateCw, Plus, Download, FileUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Pagination } from "@/components/ui/pagination"
import { cn } from "@/lib/utils"

export type AtRiskStatus = "at-risk" | "critical" | "safe"

export interface AtRiskRow {
  id: string
  itemId: string
  name: string
  contentType: string
  filterMethod: string
  quantity: number
  createdAt: string
  status: AtRiskStatus
}

const STATUS_LABELS: Record<AtRiskStatus, string> = {
  "at-risk": "At Risk",
  critical: "Critical",
  safe: "Safe",
}

const MOCK_DATA: AtRiskRow[] = [
  {
    id: "1",
    itemId: "COL-001",
    name: "Q1 Compliance Review",
    contentType: "Document",
    filterMethod: "Manual",
    quantity: 24,
    createdAt: "2025-02-20",
    status: "at-risk",
  },
  {
    id: "2",
    itemId: "COL-002",
    name: "Contract Renewals",
    contentType: "Document",
    filterMethod: "Auto",
    quantity: 12,
    createdAt: "2025-02-18",
    status: "critical",
  },
  {
    id: "3",
    itemId: "COL-003",
    name: "Client Onboarding",
    contentType: "Checklist",
    filterMethod: "Manual",
    quantity: 8,
    createdAt: "2025-02-15",
    status: "safe",
  },
  {
    id: "4",
    itemId: "COL-004",
    name: "Audit Trail Export",
    contentType: "Report",
    filterMethod: "Auto",
    quantity: 156,
    createdAt: "2025-02-10",
    status: "at-risk",
  },
  {
    id: "5",
    itemId: "COL-005",
    name: "Service Assignments",
    contentType: "List",
    filterMethod: "Manual",
    quantity: 42,
    createdAt: "2025-02-05",
    status: "safe",
  },
]

const LIMIT = 5
const TOTAL_MOCK = 200

function StatusCell({ status }: { status: AtRiskStatus }) {
  const bg =
    status === "critical"
      ? "bg-red-100 text-gray-800"
      : status === "at-risk"
        ? "bg-amber-100 text-gray-800"
        : "bg-gray-100 text-gray-700"
  return (
    <span
      className={cn(
        "inline-flex px-2 py-0.5 text-xs font-medium rounded-none",
        bg
      )}
    >
      {STATUS_LABELS[status]}
    </span>
  )
}

export interface QueryTableProps {
  title?: string
  className?: string
}

export function QueryTable({ title = "Query Table", className }: QueryTableProps) {
  const [collectionId, setCollectionId] = useState("")
  const [collectionName, setCollectionName] = useState("")
  const [filterMethod, setFilterMethod] = useState("all")
  const [contentType, setContentType] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [page, setPage] = useState(1)

  const handleReset = () => {
    setCollectionId("")
    setCollectionName("")
    setFilterMethod("all")
    setContentType("all")
    setStatusFilter("all")
    setStartDate("")
    setEndDate("")
    setPage(1)
  }

  const totalPages = Math.max(1, Math.ceil(TOTAL_MOCK / LIMIT))
  const displayData = MOCK_DATA

  return (
    <div className={cn("space-y-4", className)}>
      <h1 className="text-xl font-semibold text-[#5A626A]">{title}</h1>

      <div className="border border-[#5A626A]/20 bg-[#E6E0D7]/30 p-4 rounded-none space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[#5A626A]">Item ID</label>
            <Input
              placeholder="Enter item ID"
              value={collectionId}
              onChange={(e) => setCollectionId(e.target.value)}
              className="rounded-none border-[#5A626A]/30 bg-white"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[#5A626A]">Name</label>
            <Input
              placeholder="Enter name"
              value={collectionName}
              onChange={(e) => setCollectionName(e.target.value)}
              className="rounded-none border-[#5A626A]/30 bg-white"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[#5A626A]">Filter method</label>
            <Select value={filterMethod} onValueChange={setFilterMethod}>
              <SelectTrigger className="rounded-none border-[#5A626A]/30 bg-white text-[#5A626A] h-9 [&>svg]:text-[#5A626A]">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent className="rounded-none border-[#5A626A]/30 bg-[#E6E0D7]">
                <SelectItem value="all" className="rounded-none focus:bg-[#E6E0D7] focus:text-[#5A626A]">All</SelectItem>
                <SelectItem value="manual" className="rounded-none focus:bg-[#E6E0D7] focus:text-[#5A626A]">Manual</SelectItem>
                <SelectItem value="auto" className="rounded-none focus:bg-[#E6E0D7] focus:text-[#5A626A]">Auto</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[#5A626A]">Content type</label>
            <Select value={contentType} onValueChange={setContentType}>
              <SelectTrigger className="rounded-none border-[#5A626A]/30 bg-white text-[#5A626A] h-9 [&>svg]:text-[#5A626A]">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent className="rounded-none border-[#5A626A]/30 bg-[#E6E0D7]">
                <SelectItem value="all" className="rounded-none focus:bg-[#E6E0D7] focus:text-[#5A626A]">All</SelectItem>
                <SelectItem value="document" className="rounded-none focus:bg-[#E6E0D7] focus:text-[#5A626A]">Document</SelectItem>
                <SelectItem value="report" className="rounded-none focus:bg-[#E6E0D7] focus:text-[#5A626A]">Report</SelectItem>
                <SelectItem value="checklist" className="rounded-none focus:bg-[#E6E0D7] focus:text-[#5A626A]">Checklist</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[#5A626A]">Status</label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="rounded-none border-[#5A626A]/30 bg-white text-[#5A626A] h-9 [&>svg]:text-[#5A626A]">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent className="rounded-none border-[#5A626A]/30 bg-[#E6E0D7]">
                <SelectItem value="all" className="rounded-none focus:bg-[#E6E0D7] focus:text-[#5A626A]">All</SelectItem>
                <SelectItem value="at-risk" className="rounded-none focus:bg-[#E6E0D7] focus:text-[#5A626A]">At Risk</SelectItem>
                <SelectItem value="critical" className="rounded-none focus:bg-[#E6E0D7] focus:text-[#5A626A]">Critical</SelectItem>
                <SelectItem value="safe" className="rounded-none focus:bg-[#E6E0D7] focus:text-[#5A626A]">Safe</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[#5A626A]">Created from</label>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="rounded-none border-[#5A626A]/30 bg-white"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[#5A626A]">Created to</label>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="rounded-none border-[#5A626A]/30 bg-white"
            />
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              className="rounded-none bg-[#8BA88B] text-white hover:bg-[#7a9a7a]"
              onClick={() => setPage(1)}
            >
              <Search className="h-4 w-4 mr-1.5" />
              Query
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="rounded-none border-[#5A626A]/30 text-[#5A626A] bg-white hover:bg-[#E6E0D7]"
              onClick={handleReset}
            >
              <RotateCw className="h-4 w-4 mr-1.5" />
              Reset
            </Button>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Button className="rounded-none bg-[#8BA88B] text-white hover:bg-[#7a9a7a]">
            <Plus className="h-4 w-4 mr-1.5" />
            New
          </Button>
          <Button
            variant="secondary"
            className="rounded-none border-[#5A626A]/30 text-[#5A626A] bg-[#E6E0D7] hover:bg-[#E0DAD2]"
          >
            <FileUp className="h-4 w-4 mr-1.5" />
            Batch import
          </Button>
        </div>
        <Button
          variant="secondary"
          className="rounded-none border-[#5A626A]/30 text-[#5A626A] bg-[#E6E0D7] hover:bg-[#E0DAD2]"
        >
          <Download className="h-4 w-4 mr-1.5" />
          Download
        </Button>
      </div>

      <div className="rounded-none border border-gray-200 bg-white">
        <Table>
          <TableHeader className="border-gray-200 bg-gray-50">
            <TableRow className="border-gray-200 hover:bg-transparent [&>th]:h-8 [&>th]:py-1.5 [&>th]:px-3 [&>th]:text-xs">
              <TableHead className="font-medium text-gray-700">Item ID</TableHead>
              <TableHead className="font-medium text-gray-700">Name</TableHead>
              <TableHead className="font-medium text-gray-700">Content type</TableHead>
              <TableHead className="font-medium text-gray-700">Filter method</TableHead>
              <TableHead className="font-medium text-gray-700">Quantity</TableHead>
              <TableHead className="font-medium text-gray-700">Created</TableHead>
              <TableHead className="font-medium text-gray-700">Status</TableHead>
              <TableHead className="font-medium text-gray-700">Operation</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {displayData.map((row, idx) => (
              <TableRow
                key={row.id}
                className={cn(
                  "border-gray-100 hover:bg-gray-50/80 [&>td]:py-1.5 [&>td]:px-3 [&>td]:text-sm",
                  idx % 2 === 1 && "bg-gray-50/50"
                )}
              >
                <TableCell className="text-gray-900">{row.itemId}</TableCell>
                <TableCell className="text-gray-900">{row.name}</TableCell>
                <TableCell className="text-gray-900">{row.contentType}</TableCell>
                <TableCell className="text-gray-900">{row.filterMethod}</TableCell>
                <TableCell className="text-gray-900">{row.quantity}</TableCell>
                <TableCell className="text-gray-900">{row.createdAt}</TableCell>
                <TableCell>
                  <StatusCell status={row.status} />
                </TableCell>
                <TableCell>
                  <button
                    type="button"
                    className="text-gray-700 hover:text-gray-900 hover:underline"
                  >
                    View
                  </button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Pagination
        page={page}
        total={TOTAL_MOCK}
        limit={LIMIT}
        onPageChange={setPage}
      />
    </div>
  )
}
