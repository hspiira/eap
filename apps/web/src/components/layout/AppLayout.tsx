/**
 * Application Layout
 * Sidebar navigation layout with dark theme
 */

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
  Phone,
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
}

type NavCategory = {
  id: string
  label: string
  description: string
  items: NavItem[]
}

/**
 * Grouped navigation – not everything is a top-level module.
 * Overview: entry point
 * People: clients, contacts, persons (who we serve / who works for us)
 * Engagement & Delivery: contracts → services → assignments → sessions, activities
 * Content & Insights: documents, KPIs
 * Administration: users, audit (tenant management is in a separate app)
 */
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
    description: 'Manage clients, their contacts, tags, and client people (employees and dependents).',
    items: [
      { path: '/clients', label: 'Clients', icon: UserCircle },
      { path: '/contacts', label: 'Contacts', icon: Phone },
      { path: '/people/client-people', label: 'Client people', icon: UserCircle },
    ],
  },
  {
    id: 'engagement',
    label: 'Engagement & Delivery',
    description: 'Contracts, service catalog, assignments, delivery sessions, service providers, and client activity tracking.',
    items: [
      { path: '/contracts', label: 'Contracts', icon: FileText },
      { path: '/services', label: 'Services', icon: ClipboardList },
      { path: '/service-assignments', label: 'Service Assignments', icon: LinkIcon },
      { path: '/sessions', label: 'Sessions', icon: Calendar },
      { path: '/service-providers', label: 'Service providers', icon: UserCircle },
      { path: '/activities', label: 'Activities', icon: History },
    ],
  },
  {
    id: 'content',
    label: 'Content & Insights',
    description: 'Document management, industry classification, and key performance indicators for tracking organizational metrics.',
    items: [
      { path: '/documents', label: 'Documents', icon: FolderOpen },
      { path: '/kpis', label: 'KPIs', icon: BarChart3 },
    ],
  },
  {
    id: 'administration',
    label: 'Administration',
    description: 'User management and audit logs.',
    items: [
      { path: '/audit', label: 'Audit', icon: Shield },
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
    <div className="min-h-screen bg-calm flex flex-col">
      {/* Top Bar */}
      <header className="sticky top-0 z-30 bg-calm border-b border-[0.5px] border-safe">
        <div className="flex items-center justify-between px-6 h-16">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="hidden lg:flex p-2 text-safe hover:bg-safe-light/10 transition-colors"
            aria-label="Toggle sidebar"
          >
            <Menu size={20} />
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 text-safe hover:bg-safe-light/10 transition-colors"
            aria-label="Menu"
          >
            <Menu size={20} />
          </button>
          <div className="flex-1" />
          {/* Tenant indicator */}
          <div className="flex items-center gap-2 mr-4">
            {tenantLoading ? (
              <span className="text-sm text-safe-light">Loading…</span>
            ) : currentTenant ? (
              availableTenants.length > 1 ? (
                <select
                  value={currentTenant.id}
                  onChange={(e) => {
                    const t = availableTenants.find((x) => x.id === e.target.value)
                    if (t) setCurrentTenant(t)
                  }}
                  className="text-sm bg-calm border border-[0.5px] border-safe text-safe px-3 py-1.5 rounded-none focus:outline-none focus:border-natural"
                  aria-label="Current organization"
                >
                  {availableTenants.map((tenant) => (
                    <option key={tenant.id} value={tenant.id}>
                      {tenant.name}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="flex items-center gap-1.5 text-sm text-safe" title="Current organization">
                  <Building2 size={16} />
                  {currentTenant.name}
                </span>
              )
            ) : null}
          </div>
          <button
            onClick={logout}
            className="p-2 text-safe hover:bg-safe-light/10 transition-colors"
            aria-label="Sign out"
            title="Sign out"
          >
            <LogOut size={20} />
          </button>
        </div>
      </header>

      {/* Main Content Area with Sidebar */}
      <div className="flex flex-1">
        {/* Sidebar */}
        <aside
          className={`${
            sidebarOpen ? 'w-64' : 'w-0'
          } hidden lg:block bg-calm transition-all duration-300 ease-in-out overflow-hidden`}
        >
          <div className="flex flex-col h-[calc(100vh-4rem)] ml-4">
            <div className="p-4">
              <h2 className="text-base font-semibold text-safe">Evexía</h2>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto py-1">
              {navigationItems.map((item) => {
                if ('type' in item && item.type === 'divider') {
                  return (
                    <div
                      key={item.id}
                      className="h-px bg-safe-light/30 mx-2 my-1"
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
                      className="flex items-center gap-3 px-4 py-1.5 text-safe-light cursor-not-allowed"
                    >
                      <Icon size={18} />
                      <span className="text-sm">{navItem.label}</span>
                      <span className="ml-auto text-xs">Soon</span>
                    </div>
                  )
                }

                return (
                  <Link
                    key={navItem.path}
                    to={navItem.path}
                    className={`flex items-center gap-3 px-4 py-1.5 transition-colors ${
                      isActive
                        ? 'bg-natural text-white'
                        : 'text-safe hover:bg-safe-light/10'
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

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside className="fixed left-0 top-16 h-full w-64 bg-calm z-50 lg:hidden overflow-y-auto">
            <div className="flex flex-col h-full">
              <div className="flex items-center justify-between p-4 border-b border-[0.5px] border-safe">
                <h2 className="text-base font-semibold text-safe">Evexía</h2>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2 hover:bg-safe-light/10 rounded transition-colors"
                  aria-label="Close menu"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Navigation */}
              <nav className="flex-1 py-1 ml-4">
                {navigationItems.map((item) => {
                  if ('type' in item && item.type === 'divider') {
                    return (
                      <div
                        key={item.id}
                        className="h-px bg-safe-light/30 mx-2 my-1"
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
                        className="flex items-center gap-3 px-4 py-1.5 text-safe-light cursor-not-allowed"
                      >
                        <Icon size={18} />
                        <span className="text-sm">{navItem.label}</span>
                        <span className="ml-auto text-xs">Soon</span>
                      </div>
                    )
                  }

                  return (
                    <Link
                      key={navItem.path}
                      to={navItem.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center gap-3 px-4 py-1.5 transition-colors ${
                        isActive
                          ? 'bg-natural text-white'
                          : 'text-safe hover:bg-safe-light/10'
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

        {/* Main Content Area */}
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  )
}
