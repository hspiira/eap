import { BarChart3, Check, Heart, Settings, User, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const TABS = ["All", "Workouts", "Goals", "Social"] as const

const ACTIVITIES = [
  {
    id: "1",
    icon: BarChart3,
    iconColor: "text-accent-green",
    title: "Weekly Summary",
    badge: "Personal Record!",
    badgeClass: "bg-accent-purple text-white",
    description: "You completed 5 workouts this week.",
    time: "Today",
    actions: null,
  },
  {
    id: "2",
    icon: User,
    iconColor: "text-accent-purple",
    title: "Challenge Invitation",
    badge: null,
    badgeClass: "",
    description: 'Join the "10K Steps Daily" challenge.',
    time: "Yesterday",
    actions: (
      <>
        <Button
          variant="secondary"
          size="sm"
          className="gap-1.5 border-neutral-200 bg-white text-neutral-700 hover:bg-surface-soft"
        >
          <X className="h-3.5 w-3.5" />
          Decline
        </Button>
        <Button
          size="sm"
          className="gap-1.5 bg-accent-purple text-white hover:bg-accent-purple-dark"
        >
          <Check className="h-3.5 w-3.5" />
          Join
        </Button>
      </>
    ),
  },
  {
    id: "3",
    icon: BarChart3,
    iconColor: "text-neutral-700",
    title: "FitTracker Pro",
    badge: "5K Run",
    badgeClass: "bg-accent-pink text-white",
    description: "Your running goal was achieved.",
    time: "Yesterday",
    actions: null,
  },
  {
    id: "4",
    icon: Heart,
    iconColor: "text-accent-error-deep",
    title: "Sarah Fitness",
    badge: null,
    badgeClass: "",
    description: "Liked your workout routine.",
    time: "Yesterday",
    actions: null,
  },
]

export function ActivityFeedCard() {
  return (
    <div className="border border-neutral-200 bg-white rounded-none">
      <div className="flex items-center justify-between border-b border-neutral-100 px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-neutral-700">Activity Feed</h2>
          <span className="flex h-5 min-w-[20px] items-center justify-center bg-surface-chip px-1.5 text-xs font-medium text-neutral-700 rounded-none">
            {ACTIVITIES.length}
          </span>
        </div>
        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center text-neutral-400 hover:bg-surface-soft rounded-none"
          aria-label="Activity feed settings"
        >
          <Settings className="h-4 w-4" />
        </button>
      </div>
      <div className="flex gap-0 border-b border-neutral-100">
        {TABS.map((tab, i) => (
          <button
            key={tab}
            type="button"
            className={cn(
              "px-4 py-2.5 text-sm font-medium rounded-none",
              i === 0
                ? "bg-accent-purple text-white"
                : "text-neutral-700 hover:bg-surface-soft"
            )}
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="divide-y divide-neutral-100">
        {ACTIVITIES.map((a) => (
          <div key={a.id} className="flex gap-3 px-4 py-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-neutral-200 bg-surface-tile">
              <a.icon className={cn("h-4 w-4", a.iconColor)} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-medium text-neutral-700">{a.title}</span>
                {a.badge && (
                  <span
                    className={cn(
                      "px-1.5 py-0.5 text-xs font-medium rounded-none",
                      a.badgeClass
                    )}
                  >
                    {a.badge}
                  </span>
                )}
                <span className="ml-auto shrink-0 text-xs text-neutral-400">{a.time}</span>
              </div>
              <p className="mt-0.5 text-sm text-neutral-700/90">{a.description}</p>
              {a.actions && (
                <div className="mt-2 flex gap-2">{a.actions}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
