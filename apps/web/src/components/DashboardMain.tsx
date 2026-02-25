import { EmailCampaignCard } from "@/components/EmailCampaignCard"
import { EventCards } from "@/components/EventCards"
import { FlightProgressCard } from "@/components/FlightProgressCard"
import { MapSettingsCard } from "@/components/MapSettingsCard"
import { NotificationsCard } from "@/components/NotificationsCard"
import { OnboardingProgressCard } from "@/components/OnboardingProgressCard"
import { OnSiteBehaviorCard } from "@/components/OnSiteBehaviorCard"
import { QueryInputCard } from "@/components/QueryInputCard"
import { ErrorCard } from "@/components/ErrorCard"
import { HRDashboard } from "@/components/HRDashboard"
import { TransitionsCard } from "@/components/TransitionsCard"

export function DashboardMain({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header className="sticky top-0 z-10 flex h-10 shrink-0 items-center justify-between gap-4 border-b border-[#bfc4c9]/30 bg-[#fafafa] px-3">
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
        <div className="mx-auto grid max-w-5xl grid-cols-1 gap-4 p-4 lg:grid-cols-2">
          <div className="min-w-0">
            <FlightProgressCard />
          </div>
          <div className="min-w-0">
            <OnSiteBehaviorCard />
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
        <HRDashboard />
        <div className="grid grid-cols-1 gap-4 p-4 lg:grid-cols-12">
          <div className="min-w-0 lg:col-span-8">
            <TransitionsCard />
          </div>
          <div className="min-w-0 lg:col-span-4">
            <OnboardingProgressCard />
          </div>
        </div>
        {children}
      </div>
    </div>
  )
}
