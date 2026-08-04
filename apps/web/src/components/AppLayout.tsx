import { useEffect, useState } from "react"

import { AppSidebar } from "@/components/AppSidebar"
import { CommandPalette } from "@/components/CommandPalette"
import { FixtureBanner } from "@/components/common/FixtureBanner"
import { DashboardHeader } from "@/components/DashboardHeader"
import { DashboardMain } from "@/components/DashboardMain"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { uiStorage } from "@/lib/storage"

export function AppLayout({ children }: { children?: React.ReactNode }) {
  // Read persisted state once on mount; default to collapsed.
  const [open, setOpen] = useState<boolean>(() => {
    if (typeof window === "undefined") return false
    return uiStorage.read().sidebar_open
  })

  useEffect(() => {
    uiStorage.patch({ sidebar_open: open })
  }, [open])

  return (
    <div className="h-svh w-full bg-bg text-fg">
      <CommandPalette />
      <SidebarProvider open={open} onOpenChange={setOpen}>
        <AppSidebar />
        <SidebarInset>
          <FixtureBanner />
          <DashboardHeader />
          <div className="content-area-scroll min-h-0 flex-1 overflow-y-auto">
            {children ?? <DashboardMain />}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </div>
  )
}
