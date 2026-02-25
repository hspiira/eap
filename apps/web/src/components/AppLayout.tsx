import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/AppSidebar"
import { DashboardMain } from "@/components/DashboardMain"

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen flex-col overflow-hidden border border-t border-l border-r border-[#bfc4c9]/30 bg-[#fafafa] pt-6 px-6">
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <DashboardMain>{children}</DashboardMain>
        </SidebarInset>
      </SidebarProvider>
    </div>
  )
}
