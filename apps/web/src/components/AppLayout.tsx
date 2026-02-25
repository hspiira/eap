import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/AppSidebar"

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="pt-[var(--sidebar-row-height)] pr-[var(--sidebar-row-height)] pl-0">
        <div className="mb-5 border border-b-0 border-[#5A626A]/30 min-h-0 flex flex-col rounded-none">
          {children}
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
