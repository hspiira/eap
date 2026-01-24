/**
 * Application Layout
 * Main layout with fixed top navigation (Anduril-style)
 */

import { useState, useEffect, useRef } from 'react'
import { Link, useLocation } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { useTenant } from '@/contexts/TenantContext'
import {
  LayoutDashboard,
  Users,
  UserCircle,
  FileText,
  ClipboardList,
  Calendar,
  FolderOpen,
  FolderTree,
  BarChart3,
  Shield,
  Menu,
  X,
  LogOut,
  ChevronDown,
  Settings,
  Link as LinkIcon,
  Phone,
  History,
  Building2,
  Tag,
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
 * Administration: users, audit, tenants (platform admin)
 */
const navigationCategories: NavCategory[] = [
  {
    id: 'overview',
    label: 'Overview',
    description: 'High-level dashboard and analytics for your organization.',
    items: [
      { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, comingSoon: true },
    ],
  },
  {
    id: 'people',
    label: 'People',
    description: 'Manage clients, their contacts, tags, and client people (employees and dependents).',
    items: [
      { path: '/clients', label: 'Clients', icon: UserCircle },
      { path: '/contacts', label: 'Contacts', icon: Phone },
      { path: '/client-tags', label: 'Client Tags', icon: Tag },
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
      { path: '/industries', label: 'Industries', icon: FolderTree },
      { path: '/kpis', label: 'KPIs', icon: BarChart3 },
    ],
  },
  {
    id: 'administration',
    label: 'Administration',
    description: 'User management, audit logs, and platform administration tools.',
    items: [
      { path: '/users', label: 'Users', icon: Users },
      { path: '/audit', label: 'Audit', icon: Shield },
      { path: '/tenants', label: 'Tenants', icon: Building2, platformAdminOnly: true },
    ],
  },
]

export function AppLayout({ children }: AppLayoutProps) {
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null)
  const [profileMenuOpen, setProfileMenuOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { logout, isAuthenticated } = useAuth()
  const { currentTenant } = useTenant()
  const location = useLocation()
  const navRef = useRef<HTMLDivElement>(null)
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(event.target as Node)) {
        setActiveDropdown(null)
      }
    }

    if (activeDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [activeDropdown])

  // Close profile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const profileButton = document.querySelector('[aria-label="User menu"]')
      if (profileButton && !profileButton.contains(event.target as Node)) {
        setProfileMenuOpen(false)
      }
    }

    if (profileMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [profileMenuOpen])

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current)
      }
    }
  }, [])

  if (!isAuthenticated) {
    return <>{children}</>
  }

  const handleCategoryHover = (categoryId: string) => {
    // Clear any pending timeout
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)
      hoverTimeoutRef.current = null
    }
    setActiveDropdown(categoryId)
  }

  const handleCategoryLeave = () => {
    // Smooth delay to allow moving to dropdown
    hoverTimeoutRef.current = setTimeout(() => {
      setActiveDropdown(null)
      hoverTimeoutRef.current = null
    }, 150)
  }

  const handleDropdownEnter = () => {
    // Clear timeout when entering dropdown
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)
      hoverTimeoutRef.current = null
    }
  }

  const handleDropdownLeave = () => {
    // Smooth delay when leaving dropdown
    hoverTimeoutRef.current = setTimeout(() => {
      setActiveDropdown(null)
      hoverTimeoutRef.current = null
    }, 150)
  }

  const getVisibleCategories = () => {
    return navigationCategories.map((category) => {
      const visibleItems = category.items.filter(
        (item) => !item.platformAdminOnly
      )
      return { ...category, visibleItems }
    }).filter((category) => category.visibleItems.length > 0)
  }

  const visibleCategories = getVisibleCategories()

  return (
    <div className="min-h-screen bg-calm flex flex-col">
      {/* Fixed Top Navigation */}
      <header className={`fixed top-0 left-0 right-0 z-50 bg-calm transition-shadow duration-200 ease-in-out ${
        activeDropdown ? 'nav-shadow' : ''
      }`}>
        <div ref={navRef} className="relative">
          {/* Main Nav Bar */}
          <div className="flex items-center justify-between px-6 h-16">
            {/* Brand */}
            <div className="flex items-center">
              <Link to="/dashboard" className="text-xl font-bold text-safe">
                Evexía
              </Link>
            </div>

            {/* Desktop Navigation - Categories */}
            <nav className="hidden lg:flex items-center gap-1">
              {visibleCategories.map((category) => {
                const hasActiveItem = category.visibleItems.some((item) =>
                  location.pathname.startsWith(item.path)
                )
                const isDropdownOpen = activeDropdown === category.id

                return (
                  <div
                    key={category.id}
                    className="relative"
                    onMouseEnter={() => handleCategoryHover(category.id)}
                    onMouseLeave={handleCategoryLeave}
                  >
                    <button
                      className={`px-4 py-2 text-sm font-medium text-safe transition-all duration-200 ease-in-out rounded-none ${
                        hasActiveItem || isDropdownOpen
                          ? 'bg-natural text-white'
                          : 'hover:bg-safe-light/10'
                      }`}
                    >
                      {category.label}
                    </button>
                  </div>
                )
              })}
            </nav>

            {/* Right Side - Utility Links */}
            <div className="flex items-center gap-4">
              {currentTenant && (
                <div className="hidden md:block text-sm text-safe">
                  <span className="text-safe-light">Tenant:</span>{' '}
                  <span className="font-medium">{currentTenant.name}</span>
                </div>
              )}

              {/* Mobile Menu Button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 text-safe hover:bg-safe-light/10 transition-all duration-200 ease-in-out rounded-none"
                aria-label="Menu"
              >
                {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>

              {/* User Profile Menu */}
              <div className="relative">
                <button
                  onClick={() => setProfileMenuOpen(!profileMenuOpen)}
                  className="flex items-center gap-2 px-2 py-2 text-safe hover:bg-safe-light/10 transition-all duration-200 ease-in-out rounded-none"
                  aria-label="User menu"
                >
                  <UserCircle size={20} />
                  <ChevronDown
                    size={16}
                    className={profileMenuOpen ? 'rotate-180' : ''}
                  />
                </button>
                {profileMenuOpen && (
                  <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-[0.5px] border-safe z-50">
                    <div className="p-3 border-b border-[0.5px] border-safe">
                      <p className="text-sm font-medium text-safe">Profile</p>
                      <p className="text-xs text-safe-light mt-1">
                        User account
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setProfileMenuOpen(false)
                        // TODO: Navigate to profile/settings page
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-safe hover:bg-calm transition-all duration-150 ease-in-out"
                    >
                      <Settings size={16} />
                      <span>Settings</span>
                    </button>
                    <button
                      onClick={() => {
                        setProfileMenuOpen(false)
                        logout()
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-safe hover:bg-calm transition-all duration-150 ease-in-out border-t border-[0.5px] border-safe"
                    >
                      <LogOut size={16} />
                      <span>Sign Out</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Full-Width Dropdowns */}
          {activeDropdown && (
            <div
              className="nav-dropdown nav-shadow absolute left-0 right-0 top-full bg-calm transition-all duration-200 ease-in-out"
              onMouseEnter={handleDropdownEnter}
              onMouseLeave={handleDropdownLeave}
            >
              {(() => {
                const category = visibleCategories.find(
                  (c) => c.id === activeDropdown
                )
                if (!category) return null

                return (
                  <div className="max-w-7xl mx-auto px-6 py-8">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      {/* Left Column - Description */}
                      <div>
                        <h3 className="text-lg font-semibold uppercase tracking-wide text-safe mb-3">
                          {category.label.toUpperCase()}
                        </h3>
                        <p className="text-sm text-safe leading-relaxed">
                          {category.description}
                        </p>
                      </div>

                      {/* Right Column - Items */}
                      <div>
                        <h3 className="text-lg font-semibold uppercase tracking-wide text-safe mb-3">
                          {category.label}
                        </h3>
                        <ul className="space-y-1">
                          {category.visibleItems.map((item) => {
                            const Icon = item.icon
                            const isActive = location.pathname.startsWith(
                              item.path
                            )

                            if (item.comingSoon) {
                              return (
                                <li key={item.path}>
                                  <div className="flex items-center gap-2 px-3 py-2 text-safe-light cursor-not-allowed">
                                    <Icon size={16} />
                                    <span className="text-sm">{item.label}</span>
                                    <span className="ml-auto text-xs">Soon</span>
                                  </div>
                                </li>
                              )
                            }

                            return (
                              <li key={item.path}>
                                <Link
                                  to={item.path}
                                  onClick={() => setActiveDropdown(null)}
                                  className={`flex items-center gap-2 px-3 py-2 text-sm transition-all duration-150 ease-in-out rounded-none ${
                                    isActive
                                      ? 'bg-natural text-white'
                                      : 'text-safe hover:bg-safe-light/10'
                                  }`}
                                >
                                  <Icon size={16} />
                                  <span>+ {item.label}</span>
                                </Link>
                              </li>
                            )
                          })}
                        </ul>
                      </div>
                    </div>
                  </div>
                )
              })()}
            </div>
          )}
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-[0.5px] border-safe bg-calm">
            <nav className="p-4 space-y-2">
              {visibleCategories.map((category) => {
                return (
                  <div key={category.id} className="mb-4">
                    <h3 className="px-2 py-1 text-xs font-semibold uppercase tracking-wider text-safe-light mb-2">
                      {category.label}
                    </h3>
                    <div className="space-y-1">
                      {category.visibleItems.map((item) => {
                        const Icon = item.icon
                        const isActive = location.pathname.startsWith(
                          item.path
                        )

                        if (item.comingSoon) {
                          return (
                            <div
                              key={item.path}
                              className="flex items-center gap-2 px-2 py-1.5 text-safe-light cursor-not-allowed"
                            >
                              <Icon size={18} />
                              <span className="text-sm font-medium">
                                {item.label}
                              </span>
                              <span className="ml-auto text-xs">Soon</span>
                            </div>
                          )
                        }

                        return (
                          <Link
                            key={item.path}
                            to={item.path}
                            onClick={() => setMobileMenuOpen(false)}
                            className={`flex items-center gap-2 px-2 py-1.5 transition-all duration-150 ease-in-out rounded-none ${
                              isActive
                                ? 'bg-natural text-white'
                                : 'text-safe hover:bg-safe-light/10'
                            }`}
                          >
                            <Icon size={18} />
                            <span className="text-sm font-medium">
                              {item.label}
                            </span>
                          </Link>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-1 pt-16 lg:pt-16 p-6">{children}</main>
    </div>
  )
}
