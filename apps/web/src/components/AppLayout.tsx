import { AppSidebar } from "@/components/AppSidebar"
import { DashboardHeader } from "@/components/DashboardHeader"
import { DashboardMain } from "@/components/DashboardMain"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"

export function AppLayout({ children }: { children?: React.ReactNode }) {
  return (
    <div className="flex h-screen flex-col overflow-hidden border border-t border-l border-r border-border/30 bg-white pt-6 px-6">
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset className="flex h-full flex-col">
          <div className="flex min-h-0 flex-1 flex-col h-full">
            <DashboardHeader />
            <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto">
              {children ?? <DashboardMain />}
            </div>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </div>
  )
}
