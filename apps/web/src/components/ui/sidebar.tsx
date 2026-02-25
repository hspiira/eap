import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"

const SIDEBAR_WIDTH = "18rem"

export const sidebarStyles = {
  text: "text-black",
  textMuted: "text-black/80",
  textMutedHover: "text-black/80 hover:text-black",
  hoverBg: "hover:bg-[#E0DAD2]",
  activeBg: "bg-[#E0DAD2]",
  focusRing: "outline-none focus-visible:ring-1 focus-visible:ring-[#5A626A]",
  itemBase: "flex w-full items-center gap-1.5 px-2 py-1.5 text-sm font-medium transition-colors rounded-none",
  itemSub: "flex w-full items-center gap-1.5 px-2 py-1 text-sm transition-colors rounded-none",
  icon: "h-3.5 w-3.5 shrink-0",
  iconMuted: "opacity-70",
  contextIconBox: "flex h-6 w-6 shrink-0 items-center justify-center bg-[#D0B5B3] text-white text-sm font-bold",
  groupAction: "p-0.5 hover:bg-[#E0DAD2] rounded-none",
  border: "border-[#5A626A]/20",
  borderedRow: "border-t border-[#5A626A]/30 rounded-none bg-[#E6E0D7] h-10 flex items-center",
  borderedRowBottom: "border-b border-[#5A626A]/30",
  searchContainer: "rounded-none bg-[#ebe8e3] px-2 py-1.5",
  searchShortcut: "px-1.5 py-0.5 bg-[#5A626A]/20 rounded-none",
  iconLg: "h-5 w-5 shrink-0",
  bg: "bg-[#E6E0D7]",
} as const

const SidebarContext = React.createContext<{ open: boolean; setOpen: (v: boolean) => void } | null>(null)

function useSidebar() {
  const ctx = React.useContext(SidebarContext)
  if (!ctx) return { open: true, setOpen: () => {} }
  return ctx
}

const SidebarProvider = ({
  children,
  defaultOpen = true,
}: {
  children: React.ReactNode
  defaultOpen?: boolean
}) => {
  const [open, setOpen] = React.useState(defaultOpen)
  return (
    <SidebarContext.Provider value={{ open, setOpen }}>
      <div
        className="flex flex-row min-h-svh w-full gap-0"
        style={{
          "--sidebar-width": SIDEBAR_WIDTH,
          "--sidebar-row-height": "2.5rem",
        } as React.CSSProperties}
      >
        {children}
      </div>
    </SidebarContext.Provider>
  )
}

const Sidebar = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div">
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-sidebar="sidebar"
    className={cn(
      "flex h-svh w-[var(--sidebar-width)] min-w-[var(--sidebar-width)] flex-shrink-0 flex-col border-r rounded-none pl-[var(--sidebar-row-height)] pt-[var(--sidebar-row-height)]",
      sidebarStyles.border,
      sidebarStyles.bg,
      sidebarStyles.text,
      className
    )}
    {...props}
  />
))
Sidebar.displayName = "Sidebar"

const SidebarHeader = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div">
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col gap-1 p-1.5", className)}
    {...props}
  />
))
SidebarHeader.displayName = "SidebarHeader"

const SidebarTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<"button">
>(({ className, children, ...props }, ref) => {
  const { open, setOpen } = useSidebar()
  return (
    <button
      ref={ref}
      type="button"
      aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
      onClick={() => setOpen(!open)}
      className={cn(
        "flex items-center justify-center p-1.5 transition-colors rounded-none",
        sidebarStyles.text,
        sidebarStyles.hoverBg,
        sidebarStyles.focusRing,
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
})
SidebarTrigger.displayName = "SidebarTrigger"

const SidebarContent = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div">
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-1 flex-col gap-0.5 overflow-auto p-1.5", className)}
    {...props}
  />
))
SidebarContent.displayName = "SidebarContent"

const SidebarGroup = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div">
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("flex flex-col gap-0.5", className)} {...props} />
))
SidebarGroup.displayName = "SidebarGroup"

const SidebarGroupLabel = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & { action?: React.ReactNode }
>(({ className, action, children, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex items-center justify-between px-2 py-1 text-xs font-semibold uppercase tracking-wider",
      sidebarStyles.text,
      className
    )}
    {...props}
  >
    <span>{children}</span>
    {action}
  </div>
))
SidebarGroupLabel.displayName = "SidebarGroupLabel"

const SidebarMenu = React.forwardRef<
  HTMLUListElement,
  React.ComponentProps<"ul">
>(({ className, ...props }, ref) => (
  <ul ref={ref} className={cn("flex flex-col gap-0", className)} {...props} />
))
SidebarMenu.displayName = "SidebarMenu"

const SidebarMenuItem = React.forwardRef<
  HTMLLIElement,
  React.ComponentProps<"li">
>(({ className, ...props }, ref) => (
  <li ref={ref} className={cn("list-none", className)} {...props} />
))
SidebarMenuItem.displayName = "SidebarMenuItem"

const SidebarMenuButton = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<"button"> & { isActive?: boolean; asChild?: boolean }
>(({ className, isActive, asChild = false, children, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      ref={ref}
      className={cn(
        sidebarStyles.itemBase,
        sidebarStyles.text,
        sidebarStyles.hoverBg,
        sidebarStyles.focusRing,
        isActive && sidebarStyles.activeBg,
        className
      )}
      {...props}
    >
      {children}
    </Comp>
  )
})
SidebarMenuButton.displayName = "SidebarMenuButton"

const SidebarMenuSub = React.forwardRef<
  HTMLUListElement,
  React.ComponentProps<"ul">
>(({ className, ...props }, ref) => (
  <ul
    ref={ref}
    className={cn("ml-3 flex flex-col gap-0 border-l pl-1.5", sidebarStyles.border, className)}
    {...props}
  />
))
SidebarMenuSub.displayName = "SidebarMenuSub"

const SidebarMenuSubItem = React.forwardRef<
  HTMLLIElement,
  React.ComponentProps<"li">
>(({ className, ...props }, ref) => (
  <li ref={ref} className={cn("list-none", className)} {...props} />
))
SidebarMenuSubItem.displayName = "SidebarMenuSubItem"

const SidebarMenuSubButton = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<"button"> & { asChild?: boolean }
>(({ className, asChild = false, children, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      ref={ref}
      className={cn(
        sidebarStyles.itemSub,
        sidebarStyles.text,
        sidebarStyles.hoverBg,
        className
      )}
      {...props}
    >
      {children}
    </Comp>
  )
})
SidebarMenuSubButton.displayName = "SidebarMenuSubButton"

const SidebarInset = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div">
>(({ className, ...props }, ref) => (
  <main
    ref={ref}
    className={cn("flex-1 overflow-auto min-w-0 bg-page", className)}
    {...props}
  />
))
SidebarInset.displayName = "SidebarInset"

export {
  SidebarProvider,
  useSidebar,
  Sidebar,
  SidebarHeader,
  SidebarTrigger,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
  SidebarInset,
}
