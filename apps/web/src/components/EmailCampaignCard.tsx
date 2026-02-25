import { Info } from "lucide-react"
import { cn } from "@/lib/utils"

const sections = [
  {
    title: "Delivered",
    primaryMetric: "98.0%",
    rows: [
      { label: "SENT", value: "415,581", dot: null },
      { label: "DELIVERED", value: "98.0% (407,212)", dot: "green" },
      { label: "BOUNCED", value: "2.0% (8,369)", dot: "warning" },
    ],
    summary: "Deliverability is solid at 98%. Keep your bounce rate under 2% by removing invalid or inactive emails regularly.",
    highlight: { text: "Deliverability is solid at 98%", type: "green" },
  },
  {
    title: "Engaged",
    primaryMetric: "56.0%",
    rows: [
      { label: "OPENS", value: "56.0% (228,037)", dot: "green" },
      { label: "CLICKS", value: "1.39% (9,555)", dot: "warning" },
    ],
    summary: "Click rate is low at 1.39%. Aim for 2%+. Test stronger CTAs and refine targeting.",
    highlight: { text: "Click rate is low at 1.39%", type: "warning" },
  },
  {
    title: "Complaints",
    primaryMetric: "0.20%",
    rows: [
      { label: "UNSUBSCRIBES", value: "0.20% (820)", dot: "warning" },
      { label: "REPORTED SPAM", value: "0.00% (2)", dot: "warning" },
    ],
    summary: "Unsubscribes and complaints are fine. Keep monitoring for spikes after each campaign.",
    highlight: null,
  },
] as const

function MetricRow({
  label,
  value,
  dot,
}: {
  label: string
  value: string
  dot: "green" | "warning" | null
}) {
  const isMuted = dot === null
  return (
    <div className="flex items-baseline justify-between gap-2 py-1 text-sm">
      <div className="flex min-w-0 items-center gap-1.5">
        {dot && (
          <span
            className={cn(
              "h-1.5 w-1.5 shrink-0 rounded-full",
              dot === "green" && "bg-natural",
              dot === "warning" && "bg-[#b85c4a]"
            )}
          />
        )}
        <span className={cn("truncate", isMuted ? "text-[#5A626A]/60" : "text-[#5A626A]")}>
          {label}
        </span>
      </div>
      <span className={cn("shrink-0 tabular-nums", isMuted ? "text-[#5A626A]/70" : "text-[#5A626A]")}>
        {value}
      </span>
    </div>
  )
}

export function EmailCampaignCard() {
  return (
    <div className="w-full p-4">
      <div
        className={cn(
          "overflow-hidden border border-[#bfc4c9]/25 bg-white",
          "rounded-lg shadow-[0_1px_4px_rgba(0,0,0,0.06)]"
        )}
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {sections.map((section, i) => (
            <div
              key={section.title}
              className={cn(
                "flex flex-col p-5",
                i > 0 && "border-l border-[#bfc4c9]/25"
              )}
            >
              <div className="mb-3 flex items-center justify-between gap-2">
                <h3 className="text-sm font-medium text-[#5A626A]">{section.title}</h3>
                <button
                  type="button"
                  className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-[#5A626A]/30 text-[#5A626A]/70 hover:bg-[#5A626A]/10"
                  aria-label={`Info about ${section.title}`}
                >
                  <Info className="h-2.5 w-2.5" />
                </button>
              </div>
              <p className="mb-4 text-2xl font-bold tabular-nums text-[#5A626A]">
                {section.primaryMetric}
              </p>
              <div className="space-y-0 border-t border-[#bfc4c9]/20 pt-3">
                {section.rows.map((row) => (
                  <MetricRow
                    key={row.label}
                    label={row.label}
                    value={row.value}
                    dot={row.dot}
                  />
                ))}
              </div>
              <p className="mt-4 text-xs leading-relaxed text-[#5A626A]/90">
                {section.highlight ? (() => {
                  const { text, type } = section.highlight
                  const i = section.summary.indexOf(text)
                  if (i === -1) return section.summary
                  const before = section.summary.slice(0, i)
                  const after = section.summary.slice(i + text.length)
                  return (
                    <>
                      {before}
                      <span className={type === "green" ? "text-natural font-medium" : "text-[#b85c4a] font-medium"}>
                        {text}
                      </span>
                      {after}
                    </>
                  )
                })() : (
                  section.summary
                )}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
