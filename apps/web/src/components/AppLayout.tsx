import { AppSidebar } from "@/components/AppSidebar"
import { DashboardHeader } from "@/components/DashboardHeader"
import { DashboardMain } from "@/components/DashboardMain"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"

export function AppLayout({ children }: { children?: React.ReactNode }) {
  return (
    <div className="h-svh w-full bg-bg text-fg">
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <DashboardHeader />
          <div className="content-area-scroll min-h-0 flex-1 overflow-y-auto">
            {children ?? <DashboardMain />}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </div>
  )
}
