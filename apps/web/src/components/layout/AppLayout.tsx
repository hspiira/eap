/**
 * Application Layout
 * Main layout with sidebar navigation and header
 */

import { useState } from 'react'
import { Link, useLocation } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { useTenant } from '@/contexts/TenantContext'
import {
  LayoutDashboard,
  Building2,
  Users,
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
} from 'lucide-react'

interface AppLayoutProps {
  children: React.ReactNode
}

const navigationItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, comingSoon: true },
  { path: '/tenants', label: 'Tenants', icon: Building2 },
  { path: '/users', label: 'Users', icon: Users },
  { path: '/clients', label: 'Clients', icon: UserCircle },
  { path: '/persons', label: 'Persons', icon: UserCircle },
  { path: '/contracts', label: 'Contracts', icon: FileText },
  { path: '/services', label: 'Services', icon: ClipboardList },
  { path: '/sessions', label: 'Sessions', icon: Calendar },
  { path: '/documents', label: 'Documents', icon: FolderOpen },
  { path: '/kpis', label: 'KPIs', icon: BarChart3 },
  { path: '/audit', label: 'Audit', icon: Shield },
]

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { logout, isAuthenticated } = useAuth()
  const { currentTenant } = useTenant()
  const location = useLocation()

  if (!isAuthenticated) {
    return <>{children}</>
  }

  return (
    <div className="min-h-screen bg-calm flex">
      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-safe-dark text-white z-40 transform transition-transform duration-300 ease-in-out flex flex-col ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
      >
        <div className="flex items-center justify-between p-4 border-b border-[0.5px] border-safe">
          <h2 className="text-xl font-bold">Evexía</h2>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 hover:bg-safe transition-colors rounded-none"
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        {currentTenant && (
          <div className="p-4 border-b border-[0.5px] border-safe">
            <p className="text-xs text-safe-light mb-1">Current Tenant</p>
            <p className="text-sm font-medium">{currentTenant.name}</p>
          </div>
        )}

        <nav className="flex-1 p-4 overflow-y-auto">
          {navigationItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname.startsWith(item.path)
            
            if (item.comingSoon) {
              return (
                <div
                  key={item.path}
                  className="flex items-center gap-3 p-3 rounded-none text-safe-light cursor-not-allowed mb-2"
                >
                  <Icon size={20} />
                  <span className="font-medium">{item.label}</span>
                  <span className="ml-auto text-xs">Soon</span>
                </div>
              )
            }

            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 p-3 rounded-none transition-colors mb-2 ${
                  isActive
                    ? 'bg-natural text-white'
                    : 'text-safe-light hover:bg-safe hover:text-white'
                }`}
              >
                <Icon size={20} />
                <span className="font-medium">{item.label}</span>
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-[0.5px] border-safe">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 p-3 rounded-none text-safe-light hover:bg-safe hover:text-white transition-colors"
          >
            <LogOut size={20} />
            <span className="font-medium">Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col lg:ml-64">
        {/* Header */}
        <header className="bg-safe text-white border-b border-[0.5px] border-safe-dark lg:fixed lg:top-0 lg:left-64 lg:right-0 z-30">
          <div className="flex items-center justify-between p-4 h-[65px]">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 hover:bg-safe-dark transition-colors rounded-none"
              aria-label="Open menu"
            >
              <Menu size={24} />
            </button>
            <div className="flex-1"></div>
            {currentTenant && (
              <div className="hidden md:block text-sm">
                <span className="text-safe-light">Tenant:</span>{' '}
                <span className="font-medium">{currentTenant.name}</span>
              </div>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 lg:pt-[65px]">{children}</main>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-safe/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}
