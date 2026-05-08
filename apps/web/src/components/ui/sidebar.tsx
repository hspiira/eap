import * as React from "react"

import { Slot } from "@radix-ui/react-slot"

import { cn } from "@/lib/utils"

const SIDEBAR_WIDTH = "18rem"

export const sidebarStyles = {
  text: "text-black",
  textMuted: "text-black/80",
  textMutedHover: "text-black/80 hover:text-black",
  hoverBg: "hover:bg-surface-tile",
  activeBg: "bg-surface-tile",
  focusRing: "outline-none focus-visible:ring-1 focus-visible:ring-ink",
  itemBase: "flex w-full items-center gap-1.5 px-2 py-1.5 text-sm font-medium transition-colors rounded-none",
  itemSub: "flex w-full items-center gap-1.5 px-2 py-1 text-sm transition-colors rounded-none",
  icon: "h-3.5 w-3.5 shrink-0",
  iconMuted: "opacity-70",
  contextIconBox: "flex h-6 w-6 shrink-0 items-center justify-center bg-danger-soft text-white text-sm font-bold",
  groupAction: "p-0.5 hover:bg-surface-tile rounded-none",
  border: "border-ink/15",
  borderedRow: "border-t border-ink/20 rounded-none bg-white h-10 flex items-center",
  borderedRowBottom: "border-b border-ink/20",
  searchContainer: "rounded-none bg-neutral-50 px-2 py-1.5",
  searchShortcut: "px-1.5 py-0.5 bg-ink/15 rounded-none",
  iconLg: "h-5 w-5 shrink-0",
  bg: "bg-white",
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
        className="grid h-full min-h-0 flex-1 grid-cols-12 w-full gap-0 overflow-hidden"
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
      "col-span-3 flex min-h-0 w-full min-w-0 flex-col overflow-hidden border-l border-r border-border/30 rounded-none",
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
    className={cn("flex flex-col gap-0", className)}
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
    className={cn("mt-2 flex flex-1 flex-col gap-0.5 overflow-auto px-2", className)}
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
    className={cn("col-span-9 flex h-full min-h-0 flex-col overflow-hidden min-w-0 border-t border-r border-border/30 bg-white", className)}
    {...props}
  />
))
SidebarInset.displayName = "SidebarInset"

export {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarProvider,
  SidebarTrigger,
  useSidebar,
}
