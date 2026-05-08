import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { useState } from "react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { useAuthStore } from "@/store/slices/authSlice"
import { CallbackCaseStatus } from "@/types/enums"

export const Route = createFileRoute("/care-callbacks/worklist/")({
  component: WorklistPage,
})

const STATUS_TABS: Array<{ key: "all" | CallbackCaseStatus; label: string }> = [
  { key: "all", label: "All" },
  { key: CallbackCaseStatus.QUEUED, label: "Queued" },
  { key: CallbackCaseStatus.IN_PROGRESS, label: "In progress" },
  { key: CallbackCaseStatus.COMPLETED, label: "Completed" },
  { key: CallbackCaseStatus.NO_ANSWER, label: "No answer" },
  { key: CallbackCaseStatus.CRISIS_ESCALATED, label: "Crisis" },
]

function WorklistPage() {
  const userId = useAuthStore((s) => s.user_id) ?? "user-helen"
  const [status, setStatus] = useState<"all" | CallbackCaseStatus>("all")

  const query = useQuery({
    queryKey: ["care-callback-cases", "list", { assigned_user_id: userId, status }],
    queryFn: () =>
      careCallbacksApi.listCases({
        assigned_user_id: userId,
        status: status === "all" ? undefined : status,
      }),
  })
  const items = query.data?.items ?? []

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-5xl space-y-4">
        <header>
          <h1 className="text-xl font-semibold text-fg">My care-callback worklist</h1>
          <p className="mt-1 text-sm text-fg/70">
            Cases assigned to you — work the queue, run triage, record an outcome.
          </p>
        </header>

        <div className="flex gap-1 border-b border-fg/10">
          {STATUS_TABS.map((t) => {
            const active = status === t.key
            return (
              <button
                key={t.key}
                type="button"
                onClick={() => setStatus(t.key)}
                className={`px-3 py-1.5 text-sm border-b-2 -mb-px transition-colors ${
                  active
                    ? "border-primary text-fg font-medium"
                    : "border-transparent text-fg/60 hover:text-fg"
                }`}
              >
                {t.label}
              </button>
            )
          })}
        </div>

        {query.isPending ? (
          <p className="text-sm text-fg/60">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-fg/60">No cases matching this filter.</p>
        ) : (
          <ul className="divide-y divide-ink/10 border border-fg/20 bg-white">
            {items.map((c) => (
              <li key={c.id} className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <Link
                      to="/care-callbacks/worklist/$caseId"
                      params={{ caseId: c.id }}
                      className="text-sm font-semibold text-fg hover:text-primary hover:underline"
                    >
                      {c.person_display_name}
                    </Link>
                    <p className="mt-1 text-xs text-fg/60">
                      Campaign: {c.campaign_id} · attempts: {c.attempt_count}
                      {c.next_attempt_at
                        ? ` · next: ${new Date(c.next_attempt_at).toLocaleDateString()}`
                        : ""}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {c.crisis_flagged && (
                      <span className="border border-danger-soft/40 bg-danger-soft/10 px-2 py-0.5 text-[11px] uppercase tracking-wide text-danger-soft">
                        Crisis
                      </span>
                    )}
                    <span className="border border-fg/20 bg-neutral-50 px-2 py-0.5 text-[11px] uppercase tracking-wide text-fg">
                      {c.status}
                    </span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
