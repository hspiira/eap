import { BarChart3, User, Heart, Settings, X, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const TABS = ["All", "Workouts", "Goals", "Social"] as const

const ACTIVITIES = [
  {
    id: "1",
    icon: BarChart3,
    iconColor: "text-[#7ED321]",
    title: "Weekly Summary",
    badge: "Personal Record!",
    badgeClass: "bg-[#8B48F7] text-white",
    description: "You completed 5 workouts this week.",
    time: "Today",
    actions: null,
  },
  {
    id: "2",
    icon: User,
    iconColor: "text-[#8B48F7]",
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
          className="gap-1.5 border-[#E0E0E0] bg-white text-[#4A4A4A] hover:bg-[#F8F8FA]"
        >
          <X className="h-3.5 w-3.5" />
          Decline
        </Button>
        <Button
          size="sm"
          className="gap-1.5 bg-[#8B48F7] text-white hover:bg-[#7A3CE6]"
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
    iconColor: "text-[#4A4A4A]",
    title: "FitTracker Pro",
    badge: "5K Run",
    badgeClass: "bg-[#FF77A9] text-white",
    description: "Your running goal was achieved.",
    time: "Yesterday",
    actions: null,
  },
  {
    id: "4",
    icon: Heart,
    iconColor: "text-[#E00000]",
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
    <div className="border border-[#E0E0E0] bg-white rounded-none">
      <div className="flex items-center justify-between border-b border-[#EEEEEE] px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-[#4A4A4A]">Activity Feed</h2>
          <span className="flex h-5 min-w-[20px] items-center justify-center bg-[#E8E8E8] px-1.5 text-xs font-medium text-[#4A4A4A] rounded-none">
            {ACTIVITIES.length}
          </span>
        </div>
        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center text-[#999999] hover:bg-[#F8F8FA] rounded-none"
          aria-label="Activity feed settings"
        >
          <Settings className="h-4 w-4" />
        </button>
      </div>
      <div className="flex gap-0 border-b border-[#EEEEEE]">
        {TABS.map((tab, i) => (
          <button
            key={tab}
            type="button"
            className={cn(
              "px-4 py-2.5 text-sm font-medium rounded-none",
              i === 0
                ? "bg-[#8B48F7] text-white"
                : "text-[#4A4A4A] hover:bg-[#F8F8FA]"
            )}
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="divide-y divide-[#EEEEEE]">
        {ACTIVITIES.map((a) => (
          <div key={a.id} className="flex gap-3 px-4 py-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[#E0E0E0] bg-[#F0F0F0]">
              <a.icon className={cn("h-4 w-4", a.iconColor)} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-medium text-[#4A4A4A]">{a.title}</span>
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
                <span className="ml-auto shrink-0 text-xs text-[#999999]">{a.time}</span>
              </div>
              <p className="mt-0.5 text-sm text-[#4A4A4A]/90">{a.description}</p>
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
