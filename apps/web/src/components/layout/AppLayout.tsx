import { useState } from 'react'
import { Link, useLocation } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { useTenant } from '@/hooks/useTenant'
import {
  PieChart,
  UserCircle,
  FileText,
  ClipboardList,
  Calendar,
  FolderOpen,
  BarChart3,
  Shield,
  Menu,
  X,
  LogOut,
  Settings,
  Link as LinkIcon,
  History,
  Building2,
} from 'lucide-react'

interface AppLayoutProps {
  children: React.ReactNode
}

type NavItem = {
  path: string
  label: string
  icon: React.ComponentType<{ size?: number }>
  comingSoon?: boolean
  platformAdminOnly?: boolean
  disabled?: boolean
}

type NavCategory = {
  id: string
  label: string
  description: string
  items: NavItem[]
}

const navigationCategories: NavCategory[] = [
  {
    id: 'overview',
    label: 'Overview',
    description: 'High-level dashboard and analytics for your organization.',
    items: [
      { path: '/dashboard', label: 'Overview', icon: PieChart, comingSoon: true },
      { path: '/settings', label: 'Settings', icon: Settings },
    ],
  },
  {
    id: 'people',
    label: 'People',
    description: 'Manage clients, their contacts, tags, and roster (employees and dependents).',
    items: [
      { path: '/clients', label: 'Clients', icon: UserCircle },
      { path: '/people/client-people', label: 'Roster', icon: UserCircle },
    ],
  },
  {
    id: 'engagement',
    label: 'Engagement & Delivery',
    description: 'Contracts, service catalog, assignments, delivery sessions, service providers, and client activity tracking.',
    items: [
      { path: '/contracts', label: 'Contracts', icon: FileText, disabled: true },
      { path: '/services', label: 'Services', icon: ClipboardList, disabled: true },
      { path: '/service-assignments', label: 'Service Assignments', icon: LinkIcon, disabled: true },
      { path: '/sessions', label: 'Sessions', icon: Calendar, disabled: true },
      { path: '/service-providers', label: 'Service providers', icon: UserCircle, disabled: true },
      { path: '/activities', label: 'Activities', icon: History, disabled: true },
    ],
  },
  {
    id: 'content',
    label: 'Content & Insights',
    description: 'Document management, industry classification, and key performance indicators for tracking organizational metrics.',
    items: [
      { path: '/documents', label: 'Documents', icon: FolderOpen, disabled: true },
      { path: '/kpis', label: 'KPIs', icon: BarChart3, disabled: true },
    ],
  },
  {
    id: 'administration',
    label: 'Administration',
    description: 'User management and audit logs.',
    items: [
      { path: '/audit', label: 'Audit', icon: Shield, disabled: true },
    ],
  },
]

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { logout, isAuthenticated } = useAuth()
  const { currentTenant, availableTenants, setCurrentTenant, isLoading: tenantLoading } = useTenant()
  const location = useLocation()

  if (!isAuthenticated) {
    return <>{children}</>
  }

  // Flatten navigation items with category separators
  const getNavigationItems = () => {
    const items: Array<NavItem | { type: 'divider'; id: string }> = []
    
    navigationCategories.forEach((category, categoryIndex) => {
      const visibleItems = category.items.filter(
        (item) => !item.platformAdminOnly
      )
      
      if (visibleItems.length > 0) {
        visibleItems.forEach((item) => {
          items.push(item)
        })
        // Add divider after each category except the last
        if (categoryIndex < navigationCategories.length - 1) {
          items.push({ type: 'divider', id: `divider-${category.id}` })
        }
      }
    })
    
    return items
  }

  const navigationItems = getNavigationItems()

  return (
    <div className="bg-page flex flex-col min-h-screen">
      <header className="sticky top-0 z-30 bg-surface border-b border-[0.5px] border-border">
        <div className="flex items-center justify-between px-6 h-16">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="hidden lg:flex p-2 text-text hover:bg-surface-hover transition-colors"
            aria-label="Toggle sidebar"
          >
            <Menu size={20} />
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 text-text hover:bg-surface-hover transition-colors"
            aria-label="Menu"
          >
            <Menu size={20} />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-2 mr-4">
            {tenantLoading ? (
              <span className="text-sm text-text-muted">Loading…</span>
            ) : currentTenant ? (
              availableTenants.length > 1 ? (
                <select
                  value={currentTenant.id}
                  onChange={(e) => {
                    const t = availableTenants.find((x) => x.id === e.target.value)
                    if (t) setCurrentTenant(t)
                  }}
                  className="text-sm bg-surface border border-[0.5px] border-border text-text px-3 py-1.5 rounded-none focus:outline-none focus:border-border-focus"
                  aria-label="Current organization"
                >
                  {availableTenants.map((tenant) => (
                    <option key={tenant.id} value={tenant.id}>
                      {tenant.name}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="flex items-center gap-1.5 text-sm text-text" title="Current organization">
                  <Building2 size={16} />
                  {currentTenant.name}
                </span>
              )
            ) : null}
          </div>
          <button
            onClick={logout}
            className="p-2 text-text hover:bg-surface-hover transition-colors"
            aria-label="Sign out"
            title="Sign out"
          >
            <LogOut size={20} />
          </button>
        </div>
      </header>

      <div className="flex flex-1">
        <aside
          className={`${
            sidebarOpen ? 'w-64' : 'w-0'
          } hidden lg:block bg-surface transition-all duration-300 ease-in-out overflow-hidden`}
        >
          <div className="flex flex-col ml-4">
            <div className="p-4">
              <h2 className="text-base font-semibold text-text">Evexía</h2>
            </div>

            <nav className="flex-1 overflow-y-auto py-1">
              {navigationItems.map((item) => {
                if ('type' in item && item.type === 'divider') {
                  return (
                    <div
                      key={item.id}
                      className="h-px bg-border mx-2 my-1 opacity-50"
                    />
                  )
                }

                const navItem = item as NavItem
                const Icon = navItem.icon
                const isActive = location.pathname.startsWith(navItem.path)

                if (navItem.comingSoon) {
                  return (
                    <div
                      key={navItem.path}
                      className="flex items-center gap-3 px-4 py-1.5 text-text-muted cursor-not-allowed"
                    >
                      <Icon size={18} />
                      <span className="text-sm">{navItem.label}</span>
                      <span className="ml-auto text-xs">Soon</span>
                    </div>
                  )
                }

                if (navItem.disabled) {
                  return (
                    <div
                      key={navItem.path}
                      className="flex items-center gap-3 px-4 py-1.5 text-text-muted cursor-not-allowed"
                    >
                      <Icon size={18} />
                      <span className="text-sm">{navItem.label}</span>
                    </div>
                  )
                }

                return (
                  <Link
                    key={navItem.path}
                    to={navItem.path}
                    className={`flex items-center gap-3 px-4 py-1.5 transition-colors rounded-none ${
                        isActive
                          ? 'bg-primary text-white'
                          : 'text-text hover:bg-surface-hover'
                    }`}
                  >
                    <Icon size={18} />
                    <span className="text-sm">{navItem.label}</span>
                  </Link>
                )
              })}
            </nav>

          </div>
        </aside>

      {mobileMenuOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside className="fixed left-0 top-16 h-full w-64 bg-surface z-50 lg:hidden overflow-y-auto">
              <div className="flex flex-col h-full">
              <div className="flex items-center justify-between p-4">
                <h2 className="text-base font-semibold text-text">Evexía</h2>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2 hover:bg-surface-hover transition-colors rounded-none"
                  aria-label="Close menu"
                >
                  <X size={20} />
                </button>
              </div>

              <nav className="flex-1 py-1 ml-4">
                {navigationItems.map((item) => {
                  if ('type' in item && item.type === 'divider') {
                    return (
                      <div
                        key={item.id}
                        className="h-px bg-border mx-2 my-1 opacity-50"
                      />
                    )
                  }

                  const navItem = item as NavItem
                  const Icon = navItem.icon
                  const isActive = location.pathname.startsWith(navItem.path)

                  if (navItem.comingSoon) {
                    return (
                      <div
                        key={navItem.path}
                        className="flex items-center gap-3 px-4 py-1.5 text-text-muted cursor-not-allowed"
                      >
                        <Icon size={18} />
                        <span className="text-sm">{navItem.label}</span>
                        <span className="ml-auto text-xs">Soon</span>
                      </div>
                    )
                  }

                  if (navItem.disabled) {
                    return (
                      <div
                        key={navItem.path}
                        className="flex items-center gap-3 px-4 py-1.5 text-text-muted cursor-not-allowed"
                      >
                        <Icon size={18} />
                        <span className="text-sm">{navItem.label}</span>
                      </div>
                    )
                  }

                  return (
                    <Link
                      key={navItem.path}
                      to={navItem.path}
                      onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-4 py-1.5 transition-colors rounded-none ${
                        isActive
                          ? 'bg-primary text-white'
                          : 'text-text hover:bg-surface-hover'
                    }`}
                    >
                      <Icon size={18} />
                      <span className="text-sm">{navItem.label}</span>
                    </Link>
                  )
                })}
              </nav>

            </div>
          </aside>
        </>
      )}

        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  )
}
