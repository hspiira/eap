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
  ChevronDown,
  Settings,
  Link as LinkIcon,
} from 'lucide-react'

interface AppLayoutProps {
  children: React.ReactNode
}

// Navigation items - tenants module is for platform admins only
// Regular tenants should not see other tenants
const navigationItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, comingSoon: true },
  // { path: '/tenants', label: 'Tenants', icon: Building2 }, // Platform admin only - hidden for regular tenants
  { path: '/users', label: 'Users', icon: Users },
  { path: '/clients', label: 'Clients', icon: UserCircle },
  { path: '/persons', label: 'Persons', icon: UserCircle },
  { path: '/contracts', label: 'Contracts', icon: FileText },
  { path: '/services', label: 'Services', icon: ClipboardList },
  { path: '/service-assignments', label: 'Service Assignments', icon: LinkIcon },
  { path: '/sessions', label: 'Sessions', icon: Calendar },
  { path: '/documents', label: 'Documents', icon: FolderOpen },
  { path: '/kpis', label: 'KPIs', icon: BarChart3 },
  { path: '/audit', label: 'Audit', icon: Shield },
]

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [profileMenuOpen, setProfileMenuOpen] = useState(false)
  const { logout, isAuthenticated } = useAuth()
  const { currentTenant } = useTenant()
  const location = useLocation()

  if (!isAuthenticated) {
    return <>{children}</>
  }

  return (
    <div className="min-h-screen bg-calm flex flex-col">
      {/* Header */}
      <header className="bg-safe text-white lg:fixed lg:top-0 lg:left-0 lg:right-0 z-30">
        <div className="flex items-center justify-between p-4 h-[65px]">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 hover:bg-safe-dark transition-colors rounded-none"
              aria-label="Open menu"
            >
              <Menu size={24} />
            </button>
            <h1 className="text-xl font-bold">Evexía</h1>
          </div>
          <div className="flex items-center gap-4">
            {currentTenant && (
              <div className="hidden md:block text-sm">
                <span className="text-safe-light">Tenant:</span>{' '}
                <span className="font-medium">{currentTenant.name}</span>
              </div>
            )}
            {/* User Profile Menu */}
            <div className="relative">
              <button
                onClick={() => setProfileMenuOpen(!profileMenuOpen)}
                className="flex items-center gap-2 p-2 hover:bg-safe-dark transition-colors rounded-none"
                aria-label="User menu"
              >
                <UserCircle size={20} />
                <ChevronDown size={16} className={profileMenuOpen ? 'rotate-180' : ''} />
              </button>
              {profileMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setProfileMenuOpen(false)}
                  />
                  <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-[0.5px] border-safe shadow-lg z-50">
                    <div className="p-3 border-b border-[0.5px] border-safe">
                      <p className="text-sm font-medium text-safe">Profile</p>
                      <p className="text-xs text-safe-light mt-1">User account</p>
                    </div>
                    <button
                      onClick={() => {
                        setProfileMenuOpen(false)
                        // TODO: Navigate to profile/settings page
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-safe hover:bg-calm transition-colors"
                    >
                      <Settings size={16} />
                      <span>Settings</span>
                    </button>
                    <button
                      onClick={() => {
                        setProfileMenuOpen(false)
                        logout()
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-safe hover:bg-calm transition-colors border-t border-[0.5px] border-safe"
                    >
                      <LogOut size={16} />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 lg:pt-[65px]">
        {/* Sidebar */}
        <aside
          className={`fixed top-[65px] left-0 h-[calc(100vh-65px)] w-64 bg-calm z-40 transform transition-transform duration-300 ease-in-out flex flex-col ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } lg:translate-x-0`}
        >
          <nav className="flex-1 p-2 overflow-y-auto">
            {navigationItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname.startsWith(item.path)
              
              if (item.comingSoon) {
                return (
                  <div
                    key={item.path}
                    className="flex items-center gap-2 px-2 py-1.5 rounded-none text-safe-light cursor-not-allowed"
                  >
                    <Icon size={18} />
                    <span className="text-sm font-medium">{item.label}</span>
                    <span className="ml-auto text-xs">Soon</span>
                  </div>
                )
              }

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-2 px-2 py-1.5 rounded-none transition-colors ${
                    isActive
                      ? 'bg-natural text-white'
                      : 'text-safe hover:bg-safe-light/20'
                  }`}
                >
                  <Icon size={18} />
                  <span className="text-sm font-medium">{item.label}</span>
                </Link>
              )
            })}
          </nav>

          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 hover:bg-safe-light/20 text-safe transition-colors rounded-none"
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </aside>

        {/* Main Content */}
        <div className="flex-1 flex flex-col lg:ml-64">
          {/* Page Content */}
          <main className="flex-1 p-6">{children}</main>
        </div>
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
