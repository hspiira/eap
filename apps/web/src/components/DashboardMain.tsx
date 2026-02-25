import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { EmailCampaignCard } from "@/components/EmailCampaignCard"
import { EventCards } from "@/components/EventCards"
import { MapSettingsCard } from "@/components/MapSettingsCard"
import { NotificationsCard } from "@/components/NotificationsCard"
import { QueryInputCard } from "@/components/QueryInputCard"
import { ErrorCard } from "@/components/ErrorCard"

export function DashboardMain({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header className="sticky top-0 z-10 flex h-10 shrink-0 items-center justify-between gap-4 border-b border-[#bfc4c9]/30 bg-[#fafafa] px-3">
        <div className="flex min-w-0 flex-1 items-center gap-1">
          <button type="button" className="shrink-0 p-1.5 text-[#5A626A] hover:bg-[#E6E0D7]" aria-label="Back">
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button type="button" className="p-1.5 text-[#5A626A] hover:bg-[#E6E0D7]" aria-label="Forward">
            <ChevronRight className="h-4 w-4" />
          </button>
          <span className="ml-2 text-sm font-medium text-[#5A626A]">Gulf Oil Ltd.</span>
          <span className="text-sm text-[#5A626A]/70">/</span>
          <span className="text-sm font-medium text-[#5A626A]">Gulf Oil Asia</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-[#5A626A]">Inbox 2 new</span>
          <Button variant="secondary" size="sm" className="rounded-none text-xs">
            Mark all as read
          </Button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto grid max-w-4xl grid-cols-1 gap-4 p-4 lg:grid-cols-2">
          <div className="min-w-0">
            <MapSettingsCard />
          </div>
          <div className="min-w-0">
            <NotificationsCard />
          </div>
        </div>
        <EmailCampaignCard />
        <div className="grid grid-cols-1 gap-4 p-4 lg:grid-cols-2">
          <div className="min-w-0">
            <EventCards />
          </div>
          <div className="flex min-w-0 flex-col gap-4">
            <QueryInputCard />
            <ErrorCard />
          </div>
        </div>
        {children}
      </div>
    </div>
  )
}
