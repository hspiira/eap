import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Breadcrumb } from '@/components/common/Breadcrumb'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/contexts/ToastContext'
import { useTenant } from '@/hooks/useTenant'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { StatusBadge } from '@/components/common/StatusBadge'
import { QRCode } from '@/components/common/QRCode'
import { IndustriesTab } from '@/routes/settings/-IndustriesTab'
import { UsersTab } from '@/routes/settings/-UsersTab'
import { ClientTagsTab } from '@/routes/settings/-ClientTagsTab'
import { ContactsTab } from '@/routes/settings/-ContactsTab'
import { usersApi, type TwoFactorSetupResponse, type TwoFactorVerifyResponse } from '@/api/endpoints/users'
import type { ApiError } from '@/types/api'
import type { User } from '@/types/entities'
import {
  User as UserIcon,
  FolderTree,
  Users,
  Tag,
  Phone,
  Palette,
  Shield,
  Bell,
  Info,
  LogOut,
  ExternalLink,
  Plus,
} from 'lucide-react'

const PREFERENCE_KEYS = {
  language: 'evexia_pref_language',
  timezone: 'evexia_pref_timezone',
  dateFormat: 'evexia_pref_date_format',
  weekStartsOn: 'evexia_pref_week_starts',
  emailNotifications: 'evexia_pref_email_notifications',
  assignmentAlerts: 'evexia_pref_assignment_alerts',
  sessionReminders: 'evexia_pref_session_reminders',
  weeklyDigest: 'evexia_pref_weekly_digest',
  sessionTimeout: 'evexia_pref_session_timeout',
} as const

const TAB_IDS = [
  'account',
  'industries',
  'users',
  'client-tags',
  'contacts',
  'preferences',
  'security',
  'notifications',
  'about',
] as const
type TabId = (typeof TAB_IDS)[number]

const TABS: { id: TabId; label: string; icon: React.ComponentType<{ size?: number }> }[] = [
  { id: 'account', label: 'Account', icon: UserIcon },
  { id: 'industries', label: 'Industries', icon: FolderTree },
  { id: 'users', label: 'Users', icon: Users },
  { id: 'client-tags', label: 'Client tags', icon: Tag },
  { id: 'contacts', label: 'Contacts', icon: Phone },
  { id: 'preferences', label: 'Preferences', icon: Palette },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'about', label: 'About', icon: Info },
]

export const Route = createFileRoute('/settings/')({
  validateSearch: (search: Record<string, unknown>) => ({
    tab: TAB_IDS.includes(search?.tab as TabId) ? (search.tab as TabId) : 'account',
  }),
  component: SettingsPage,
})

function SettingsPage() {
  const navigate = useNavigate()
  const { tab } = Route.useSearch()
  const { isAuthenticated, isLoading: authLoading, logout, user_id } = useAuth()
  const { showSuccess, showError } = useToast()
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [userLoading, setUserLoading] = useState(false)

  const setTab = (t: TabId) => navigate({ to: '/settings', search: { tab: t } })

  // Preferences (localStorage)
  const [language, setLanguage] = useState(() =>
    typeof window !== 'undefined' ? localStorage.getItem(PREFERENCE_KEYS.language) || 'en' : 'en'
  )
  const [timezone, setTimezone] = useState(() =>
    typeof window !== 'undefined' ? localStorage.getItem(PREFERENCE_KEYS.timezone) || 'UTC' : 'UTC'
  )
  const [dateFormat, setDateFormat] = useState(() =>
    typeof window !== 'undefined' ? localStorage.getItem(PREFERENCE_KEYS.dateFormat) || 'YYYY-MM-DD' : 'YYYY-MM-DD'
  )
  const [weekStartsOn, setWeekStartsOn] = useState(() =>
    typeof window !== 'undefined' ? localStorage.getItem(PREFERENCE_KEYS.weekStartsOn) || 'mon' : 'mon'
  )
  const [prefsSaving, setPrefsSaving] = useState(false)

  // Security
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [securitySaving, setSecuritySaving] = useState(false)
  const [securityErrors, setSecurityErrors] = useState<Record<string, string>>({})
  const [sessionTimeout, setSessionTimeout] = useState(() =>
    typeof window !== 'undefined' ? localStorage.getItem(PREFERENCE_KEYS.sessionTimeout) || '30' : '30'
  )

  // Notifications
  const [emailNotifs, setEmailNotifs] = useState(() => {
    if (typeof window === 'undefined') return true
    const v = localStorage.getItem(PREFERENCE_KEYS.emailNotifications)
    return v === null ? true : v === 'true'
  })
  const [assignmentAlerts, setAssignmentAlerts] = useState(() => {
    if (typeof window === 'undefined') return true
    const v = localStorage.getItem(PREFERENCE_KEYS.assignmentAlerts)
    return v === null ? true : v === 'true'
  })
  const [sessionReminders, setSessionReminders] = useState(() => {
    if (typeof window === 'undefined') return true
    const v = localStorage.getItem(PREFERENCE_KEYS.sessionReminders)
    return v === null ? true : v === 'true'
  })
  const [weeklyDigest, setWeeklyDigest] = useState(() => {
    if (typeof window === 'undefined') return false
    const v = localStorage.getItem(PREFERENCE_KEYS.weeklyDigest)
    return v === 'true'
  })
  const [notifSaving, setNotifSaving] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate({ to: '/auth/login', search: {} })
    }
  }, [isAuthenticated, authLoading, navigate])

  // Fetch current user data when on account or security tab
  useEffect(() => {
    if ((tab === 'account' || tab === 'security') && user_id && isAuthenticated && !authLoading) {
      const fetchUser = async () => {
        try {
          setUserLoading(true)
          const user = await usersApi.getById(user_id)
          setCurrentUser(user)
        } catch (error) {
          console.error('Failed to fetch user data:', error)
          // Don't show error toast here - user can still see logout button
        } finally {
          setUserLoading(false)
        }
      }
      fetchUser()
    }
  }, [tab, user_id, isAuthenticated, authLoading])

  // Fetch user preferences on mount/login
  useEffect(() => {
    if (user_id && isAuthenticated && !authLoading) {
      const fetchPreferences = async () => {
        try {
          const user = await usersApi.getById(user_id)
          // Update state from backend, fallback to localStorage if not set
          if (user.preferred_language) {
            setLanguage(user.preferred_language)
            localStorage.setItem(PREFERENCE_KEYS.language, user.preferred_language)
          }
          if (user.timezone) {
            setTimezone(user.timezone)
            localStorage.setItem(PREFERENCE_KEYS.timezone, user.timezone)
          }
          if (user.date_format) {
            setDateFormat(user.date_format)
            localStorage.setItem(PREFERENCE_KEYS.dateFormat, user.date_format)
          }
          if (user.week_starts_on) {
            setWeekStartsOn(user.week_starts_on)
            localStorage.setItem(PREFERENCE_KEYS.weekStartsOn, user.week_starts_on)
          }
          // Notification preferences
          if (user.email_notifications !== null && user.email_notifications !== undefined) {
            setEmailNotifs(user.email_notifications)
            localStorage.setItem(PREFERENCE_KEYS.emailNotifications, String(user.email_notifications))
          }
          if (user.assignment_alerts !== null && user.assignment_alerts !== undefined) {
            setAssignmentAlerts(user.assignment_alerts)
            localStorage.setItem(PREFERENCE_KEYS.assignmentAlerts, String(user.assignment_alerts))
          }
          if (user.session_reminders !== null && user.session_reminders !== undefined) {
            setSessionReminders(user.session_reminders)
            localStorage.setItem(PREFERENCE_KEYS.sessionReminders, String(user.session_reminders))
          }
          if (user.weekly_digest !== null && user.weekly_digest !== undefined) {
            setWeeklyDigest(user.weekly_digest)
            localStorage.setItem(PREFERENCE_KEYS.weeklyDigest, String(user.weekly_digest))
          }
        } catch (error) {
          console.error('Failed to fetch user preferences:', error)
          // Fallback to localStorage values (already set in useState initializers)
        }
      }
      fetchPreferences()
    }
  }, [user_id, isAuthenticated, authLoading])

  const savePreferences = async () => {
    if (!user_id) {
      // Fallback to localStorage only if not authenticated
      setPrefsSaving(true)
      try {
        localStorage.setItem(PREFERENCE_KEYS.language, language)
        localStorage.setItem(PREFERENCE_KEYS.timezone, timezone)
        localStorage.setItem(PREFERENCE_KEYS.dateFormat, dateFormat)
        localStorage.setItem(PREFERENCE_KEYS.weekStartsOn, weekStartsOn)
        localStorage.setItem(PREFERENCE_KEYS.sessionTimeout, sessionTimeout)
        showSuccess('Preferences saved')
      } catch {
        showError('Failed to save preferences')
      } finally {
        setPrefsSaving(false)
      }
      return
    }

    setPrefsSaving(true)
    try {
      // Save to backend
      await usersApi.updatePreferences(user_id, {
        preferred_language: language,
        timezone: timezone,
        date_format: dateFormat,
        week_starts_on: weekStartsOn,
      })

      // Also save to localStorage as cache/fallback
      localStorage.setItem(PREFERENCE_KEYS.language, language)
      localStorage.setItem(PREFERENCE_KEYS.timezone, timezone)
      localStorage.setItem(PREFERENCE_KEYS.dateFormat, dateFormat)
      localStorage.setItem(PREFERENCE_KEYS.weekStartsOn, weekStartsOn)
      localStorage.setItem(PREFERENCE_KEYS.sessionTimeout, sessionTimeout)

      showSuccess('Preferences saved')
    } catch (error) {
      if (error instanceof Error && 'status' in error) {
        const apiError = error as ApiError
        showError(apiError.message || 'Failed to save preferences')
      } else {
        showError('Failed to save preferences')
      }
    } finally {
      setPrefsSaving(false)
    }
  }

  const handleSecuritySubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const err: Record<string, string> = {}
    if (!currentPassword) err.currentPassword = 'Required'
    if (!newPassword) err.newPassword = 'Required'
    else if (newPassword.length < 8) err.newPassword = 'Min 8 characters'
    if (newPassword !== confirmPassword) err.confirmPassword = 'Must match'
    setSecurityErrors(err)
    if (Object.keys(err).length > 0) return

    if (!user_id) {
      showError('User ID not available. Please log in again.')
      return
    }

    setSecuritySaving(true)
    try {
      await usersApi.updatePassword(user_id, {
        current_password: currentPassword,
        password: newPassword,
      })
      showSuccess('Password updated successfully')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setSecurityErrors({})
    } catch (error) {
      if (error instanceof Error && 'status' in error) {
        const apiError = error as ApiError
        if (apiError.fieldErrors) {
          setSecurityErrors(apiError.fieldErrors)
        } else if (apiError.status === 400 || apiError.status === 401) {
          setSecurityErrors({ currentPassword: apiError.message || 'Current password is incorrect' })
        } else {
          showError(apiError.message || 'Failed to update password')
        }
      } else {
        showError('Failed to update password')
      }
    } finally {
      setSecuritySaving(false)
    }
  }

  const saveNotifications = async () => {
    if (!user_id) {
      // Fallback to localStorage only if not authenticated
      setNotifSaving(true)
      try {
        localStorage.setItem(PREFERENCE_KEYS.emailNotifications, String(emailNotifs))
        localStorage.setItem(PREFERENCE_KEYS.assignmentAlerts, String(assignmentAlerts))
        localStorage.setItem(PREFERENCE_KEYS.sessionReminders, String(sessionReminders))
        localStorage.setItem(PREFERENCE_KEYS.weeklyDigest, String(weeklyDigest))
        showSuccess('Notifications saved')
      } catch {
        showError('Failed to save')
      } finally {
        setNotifSaving(false)
      }
      return
    }

    setNotifSaving(true)
    try {
      // Save to backend
      await usersApi.updatePreferences(user_id, {
        email_notifications: emailNotifs,
        assignment_alerts: assignmentAlerts,
        session_reminders: sessionReminders,
        weekly_digest: weeklyDigest,
      })

      // Also save to localStorage as cache/fallback
      localStorage.setItem(PREFERENCE_KEYS.emailNotifications, String(emailNotifs))
      localStorage.setItem(PREFERENCE_KEYS.assignmentAlerts, String(assignmentAlerts))
      localStorage.setItem(PREFERENCE_KEYS.sessionReminders, String(sessionReminders))
      localStorage.setItem(PREFERENCE_KEYS.weeklyDigest, String(weeklyDigest))

      showSuccess('Notifications saved')
    } catch (error) {
      if (error instanceof Error && 'status' in error) {
        const apiError = error as ApiError
        showError(apiError.message || 'Failed to save notifications')
      } else {
        showError('Failed to save notifications')
      }
    } finally {
      setNotifSaving(false)
    }
  }

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <Breadcrumb items={[{ label: 'Settings' }]} className="mb-2" />

        <div className="border-b border-safe/30 mb-4">
          <nav className="flex" aria-label="Settings tabs">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`flex items-center gap-2 px-3 py-2.5 text-sm font-medium transition-colors rounded-none ${
                  tab === id
                    ? 'bg-calm-dark text-natural'
                    : 'text-safe hover:bg-calm hover:text-natural'
                }`}
              >
                <Icon size={18} />
                {label}
              </button>
            ))}
          </nav>
        </div>

        <div className="bg-white border border-[0.5px] border-safe/30 p-4">
          {tab === 'account' && (
            <AccountTab
              onLogout={logout}
              user={currentUser}
              loading={userLoading}
            />
          )}
          {tab === 'industries' && <IndustriesTab />}
          {tab === 'users' && <UsersTab />}
          {tab === 'client-tags' && <ClientTagsTab />}
          {tab === 'contacts' && <ContactsTab />}
          {tab === 'preferences' && (
            <PreferencesTab
              language={language}
              setLanguage={setLanguage}
              timezone={timezone}
              setTimezone={setTimezone}
              dateFormat={dateFormat}
              setDateFormat={setDateFormat}
              weekStartsOn={weekStartsOn}
              setWeekStartsOn={setWeekStartsOn}
              sessionTimeout={sessionTimeout}
              setSessionTimeout={setSessionTimeout}
              saving={prefsSaving}
              onSave={savePreferences}
            />
          )}
          {tab === 'security' && (
            <SecurityTab
              currentPassword={currentPassword}
              setCurrentPassword={setCurrentPassword}
              newPassword={newPassword}
              setNewPassword={setNewPassword}
              confirmPassword={confirmPassword}
              setConfirmPassword={setConfirmPassword}
              errors={securityErrors}
              saving={securitySaving}
              onSubmit={handleSecuritySubmit}
              user={currentUser}
              user_id={user_id}
              onUserUpdate={() => {
                // Refresh user data after 2FA changes
                if (user_id) {
                  usersApi.getById(user_id).then(setCurrentUser).catch(console.error)
                }
              }}
            />
          )}
          {tab === 'notifications' && (
            <NotificationsTab
              emailNotifications={emailNotifs}
              setEmailNotifications={(v) => setEmailNotifs(v)}
              assignmentAlerts={assignmentAlerts}
              setAssignmentAlerts={(v) => setAssignmentAlerts(v)}
              sessionReminders={sessionReminders}
              setSessionReminders={(v) => setSessionReminders(v)}
              weeklyDigest={weeklyDigest}
              setWeeklyDigest={(v) => setWeeklyDigest(v)}
              saving={notifSaving}
              onSave={saveNotifications}
            />
          )}
          {tab === 'about' && <AboutTab />}
        </div>
      </div>
    </AppLayout>
  )
}

function SettingsRow({
  label,
  children,
  description,
}: {
  label: string
  children: React.ReactNode
  description?: string
}) {
  return (
    <div className="py-1.5 border-b border-safe/20 last:border-0 first:pt-0">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="text-sm font-medium text-safe">{label}</div>
          {description && <div className="text-xs text-safe-light mt-0.5">{description}</div>}
        </div>
        <div className="flex-shrink-0">{children}</div>
      </div>
    </div>
  )
}

function Switch({
  checked,
  onChange,
  ariaLabel,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  ariaLabel: string
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={ariaLabel}
      onClick={() => onChange(!checked)}
      className={`relative inline-block h-5 w-9 flex-shrink-0 !rounded-full border-[0.5px] transition-colors ${
        checked ? 'bg-natural border-natural' : 'bg-white border-safe/30'
      }`}
      style={{ borderRadius: '9999px' }}
    >
      <span
        className={`absolute top-0.5 block h-4 w-4 !rounded-full bg-white border border-safe/30 transition-transform ${
          checked ? 'left-[18px]' : 'left-0.5'
        }`}
        style={{ borderRadius: '9999px' }}
      />
    </button>
  )
}

function AccountTab({
  onLogout,
  user,
  loading,
}: {
  onLogout: () => void
  user: User | null
  loading: boolean
}) {
  const { currentTenant, availableTenants, setCurrentTenant, isLoading: tenantLoading, refreshTenantsList } = useTenant()
  const [switchingTenant, setSwitchingTenant] = useState(false)

  const formatDate = (date: string | null | undefined) => {
    if (!date) return '—'
    return new Date(date).toLocaleString()
  }

  // Load available tenants if user might have multiple
  useEffect(() => {
    if (availableTenants.length === 0 && !tenantLoading) {
      refreshTenantsList().catch(console.error)
    }
  }, [availableTenants.length, tenantLoading, refreshTenantsList])

  const handleTenantChange = async (tenantId: string) => {
    const tenant = availableTenants.find((t) => t.id === tenantId)
    if (tenant && tenant.id !== currentTenant?.id) {
      setSwitchingTenant(true)
      try {
        setCurrentTenant(tenant)
        // Page will refresh context, but we can also reload to ensure clean state
        window.location.reload()
      } catch (error) {
        console.error('Failed to switch tenant:', error)
      } finally {
        setSwitchingTenant(false)
      }
    }
  }

  const hasMultipleTenants = availableTenants.length > 1

  return (
    <div className="space-y-0">
      <h2 className="text-sm font-semibold text-safe mb-1.5">Tenant</h2>
      {tenantLoading ? (
        <div className="py-2 flex items-center justify-center">
          <LoadingSpinner size="sm" />
        </div>
      ) : currentTenant ? (
        <>
          <SettingsRow label="Name">
            <span className="text-sm text-safe">{currentTenant.name}</span>
          </SettingsRow>
          {currentTenant.code && (
            <SettingsRow label="Code" description="Unique identifier for this tenant.">
              <span className="text-sm text-safe font-mono">{currentTenant.code}</span>
            </SettingsRow>
          )}
          <SettingsRow label="Status">
            <StatusBadge status={currentTenant.status} size="sm" />
          </SettingsRow>
          {currentTenant.subscription_tier && (
            <SettingsRow label="Subscription" description="Current subscription tier.">
              <span className="text-sm text-safe">{currentTenant.subscription_tier}</span>
            </SettingsRow>
          )}
          {hasMultipleTenants && (
            <SettingsRow label="Switch tenant" description="You have access to multiple tenants.">
              <Select
                name="tenant-select"
                value={currentTenant.id}
                onChange={(value) => handleTenantChange(value as string)}
                options={availableTenants.map((t) => ({
                  value: t.id,
                  label: t.name,
                }))}
                compact
                disabled={switchingTenant}
              />
            </SettingsRow>
          )}
        </>
      ) : (
        <div className="py-2 text-sm text-safe-light">No tenant information available</div>
      )}

      <h2 className="text-sm font-semibold text-safe mt-4 mb-1.5">Profile</h2>
      {loading ? (
        <div className="py-4 flex items-center justify-center">
          <LoadingSpinner size="sm" />
        </div>
      ) : user ? (
        <>
          <SettingsRow label="Email">
            <span className="text-sm text-safe">{user.email}</span>
          </SettingsRow>
          <SettingsRow label="Status">
            <StatusBadge status={user.status} size="sm" />
          </SettingsRow>
          <SettingsRow label="Email verified" description="Whether your email address has been verified.">
            <span className="text-sm text-safe">
              {user.is_email_verified ? 'Yes' : 'No'}
              {user.email_verified_at && (
                <span className="text-xs text-safe-light ml-1">
                  ({new Date(user.email_verified_at).toLocaleDateString()})
                </span>
              )}
            </span>
          </SettingsRow>
          <SettingsRow label="Two-factor authentication" description="Additional security for your account.">
            <span className="text-sm text-safe">
              {user.is_two_factor_enabled ? 'Enabled' : 'Disabled'}
            </span>
          </SettingsRow>
          <SettingsRow label="Last login" description="When you last signed in.">
            <span className="text-sm text-safe">{formatDate(user.last_login_at)}</span>
          </SettingsRow>
        </>
      ) : (
        <div className="py-2 text-sm text-safe-light">Unable to load user information</div>
      )}

      <h2 className="text-sm font-semibold text-safe mt-4 mb-1.5">Session</h2>
      <SettingsRow label="Signed in" description="Sign out to end your session.">
        <button
          onClick={onLogout}
          className="flex items-center gap-1 px-2 py-1 text-sm bg-nurturing hover:bg-nurturing-dark text-white rounded-none transition-colors"
        >
          <LogOut size={14} />
          Sign out
        </button>
      </SettingsRow>
    </div>
  )
}

function ManageLinkTab({
  label,
  path,
  description,
}: {
  label: string
  path: string
  description: string
}) {
  return (
    <div className="space-y-0">
      <h2 className="text-sm font-semibold text-safe mb-1.5">{label}</h2>
      <p className="text-xs text-safe-light mb-2">{description}</p>
      <div className="flex flex-wrap gap-1.5">
        <Link
          to={path}
          className="inline-flex items-center gap-1 px-2 py-1 text-sm border border-[0.5px] border-safe/30 text-safe hover:bg-safe-light/10 rounded-none transition-colors"
        >
          <ExternalLink size={14} />
          Manage {label}
        </Link>
        <Link
          to={`${path}/new`}
          className="inline-flex items-center gap-1 px-2 py-1 text-sm bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
        >
          <Plus size={14} />
          Create new
        </Link>
      </div>
    </div>
  )
}


function PreferencesTab({
  language,
  setLanguage,
  timezone,
  setTimezone,
  dateFormat,
  setDateFormat,
  weekStartsOn,
  setWeekStartsOn,
  sessionTimeout,
  setSessionTimeout,
  saving,
  onSave,
}: {
  language: string
  setLanguage: (v: string) => void
  timezone: string
  setTimezone: (v: string) => void
  dateFormat: string
  setDateFormat: (v: string) => void
  weekStartsOn: string
  setWeekStartsOn: (v: string) => void
  sessionTimeout: string
  setSessionTimeout: (v: string) => void
  saving: boolean
  onSave: () => void
}) {
  const langOpts = [
    { value: 'en', label: 'English' },
    { value: 'fi', label: 'Suomi' },
    { value: 'sv', label: 'Svenska' },
  ]
  const tzOpts = [
    { value: 'UTC', label: 'UTC' },
    { value: 'Europe/Helsinki', label: 'Europe/Helsinki' },
    { value: 'Europe/Stockholm', label: 'Europe/Stockholm' },
    { value: 'America/New_York', label: 'America/New York' },
    { value: 'America/Los_Angeles', label: 'America/Los Angeles' },
  ]
  const dateOpts = [
    { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
    { value: 'DD.MM.YYYY', label: 'DD.MM.YYYY' },
    { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
  ]
  const weekOpts = [
    { value: 'mon', label: 'Monday' },
    { value: 'sun', label: 'Sunday' },
  ]
  const timeoutOpts = [
    { value: '15', label: '15 min' },
    { value: '30', label: '30 min' },
    { value: '60', label: '1 hour' },
    { value: '120', label: '2 hours' },
    { value: '480', label: '8 hours' },
  ]
  return (
    <div className="space-y-0">
      <h2 className="text-sm font-semibold text-safe mb-1.5">Display & locale</h2>
      <form onSubmit={(e) => { e.preventDefault(); onSave(); }} className="space-y-1">
        <Select
          name="language"
          label="Language"
          value={language}
          onChange={(v) => setLanguage(v as string)}
          options={langOpts}
          compact
        />
        <Select
          name="timezone"
          label="Timezone"
          value={timezone}
          onChange={(v) => setTimezone(v as string)}
          options={tzOpts}
          compact
        />
        <Select
          name="dateFormat"
          label="Date format"
          value={dateFormat}
          onChange={(v) => setDateFormat(v as string)}
          options={dateOpts}
          compact
        />
        <Select
          name="weekStartsOn"
          label="Week starts on"
          value={weekStartsOn}
          onChange={(v) => setWeekStartsOn(v as string)}
          options={weekOpts}
          compact
        />
        <h2 className="text-sm font-semibold text-safe mt-2 mb-1.5">Security</h2>
        <Select
          name="sessionTimeout"
          label="Session timeout"
          value={sessionTimeout}
          onChange={(v) => setSessionTimeout(v as string)}
          options={timeoutOpts}
          compact
        />
        <div className="pt-1">
          <button
            type="submit"
            disabled={saving}
            className="px-2 py-1 text-sm bg-natural hover:bg-natural-dark text-white rounded-none transition-colors disabled:opacity-50 flex items-center gap-1"
          >
            {saving && <LoadingSpinner size="sm" color="white" />}
            Save
          </button>
        </div>
      </form>
    </div>
  )
}

function SecurityTab({
  currentPassword,
  setCurrentPassword,
  newPassword,
  setNewPassword,
  confirmPassword,
  setConfirmPassword,
  errors,
  saving,
  onSubmit,
  user,
  user_id,
  onUserUpdate,
}: {
  currentPassword: string
  setCurrentPassword: (v: string) => void
  newPassword: string
  setNewPassword: (v: string) => void
  confirmPassword: string
  setConfirmPassword: (v: string) => void
  errors: Record<string, string>
  saving: boolean
  onSubmit: (e: React.FormEvent) => void
  user: User | null
  user_id: string | null
  onUserUpdate: () => void
}) {
  const { showSuccess, showError } = useToast()
  const [twoFactorSetup, setTwoFactorSetup] = useState<TwoFactorSetupResponse | null>(null)
  const [twoFactorCode, setTwoFactorCode] = useState('')
  const [twoFactorVerifying, setTwoFactorVerifying] = useState(false)
  const [twoFactorSettingUp, setTwoFactorSettingUp] = useState(false)
  const [twoFactorDisabling, setTwoFactorDisabling] = useState(false)
  const [twoFactorError, setTwoFactorError] = useState<string | null>(null)
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null)
  const [showRecoveryCodes, setShowRecoveryCodes] = useState(false)

  const handleSetup2FA = async () => {
    if (!user_id) {
      showError('User ID not available. Please log in again.')
      return
    }

    setTwoFactorSettingUp(true)
    setTwoFactorError(null)
    try {
      const setup = await usersApi.setup2FA(user_id)
      setTwoFactorSetup(setup)
    } catch (error) {
      if (error instanceof Error && 'status' in error) {
        const apiError = error as ApiError
        setTwoFactorError(apiError.message || 'Failed to setup 2FA')
      } else {
        setTwoFactorError('Failed to setup 2FA')
      }
    } finally {
      setTwoFactorSettingUp(false)
    }
  }

  const handleVerify2FA = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user_id) {
      showError('User ID not available. Please log in again.')
      return
    }

    if (!twoFactorCode || twoFactorCode.length !== 6) {
      setTwoFactorError('Please enter a valid 6-digit code')
      return
    }

    setTwoFactorVerifying(true)
    setTwoFactorError(null)
    try {
      const result = await usersApi.verify2FA(user_id, { code: twoFactorCode })
      if (result.verified) {
        // Enable 2FA
        await usersApi.enable2FA(user_id)
        showSuccess('Two-factor authentication enabled successfully')
        setTwoFactorSetup(null)
        setTwoFactorCode('')
        if (result.recovery_codes) {
          setRecoveryCodes(result.recovery_codes)
          setShowRecoveryCodes(true)
        }
        // Refresh user data to show updated 2FA status
        onUserUpdate()
      } else {
        setTwoFactorError('Invalid verification code. Please try again.')
      }
    } catch (error) {
      if (error instanceof Error && 'status' in error) {
        const apiError = error as ApiError
        setTwoFactorError(apiError.message || 'Failed to verify code')
      } else {
        setTwoFactorError('Failed to verify code')
      }
    } finally {
      setTwoFactorVerifying(false)
    }
  }

  const handleDisable2FA = async () => {
    if (!user_id) {
      showError('User ID not available. Please log in again.')
      return
    }

    if (!confirm('Are you sure you want to disable two-factor authentication? This will make your account less secure.')) {
      return
    }

    setTwoFactorDisabling(true)
    setTwoFactorError(null)
    try {
      await usersApi.disable2FA(user_id)
      showSuccess('Two-factor authentication disabled')
      setRecoveryCodes(null)
      setShowRecoveryCodes(false)
      // Refresh user data
      onUserUpdate()
    } catch (error) {
      if (error instanceof Error && 'status' in error) {
        const apiError = error as ApiError
        setTwoFactorError(apiError.message || 'Failed to disable 2FA')
      } else {
        setTwoFactorError('Failed to disable 2FA')
      }
    } finally {
      setTwoFactorDisabling(false)
    }
  }

  const cancel2FASetup = () => {
    setTwoFactorSetup(null)
    setTwoFactorCode('')
    setTwoFactorError(null)
  }

  const is2FAEnabled = user?.is_two_factor_enabled ?? false

  return (
    <div className="space-y-0">
      <h2 className="text-sm font-semibold text-safe mb-1.5">Password</h2>
      <form onSubmit={onSubmit} className="space-y-1">
        <FormField
          label="Current password"
          name="currentPassword"
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          error={errors.currentPassword}
          compact
          placeholder="••••••••"
        />
        <FormField
          label="New password"
          name="newPassword"
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          error={errors.newPassword}
          compact
          placeholder="••••••••"
        />
        <FormField
          label="Confirm new password"
          name="confirmPassword"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          error={errors.confirmPassword}
          compact
          placeholder="••••••••"
        />
        <div className="pt-1">
          <button
            type="submit"
            disabled={saving}
            className="px-2 py-1 text-sm bg-natural hover:bg-natural-dark text-white rounded-none transition-colors disabled:opacity-50 flex items-center gap-1"
          >
            {saving && <LoadingSpinner size="sm" color="white" />}
            Update password
          </button>
        </div>
      </form>

      <h2 className="text-sm font-semibold text-safe mt-4 mb-1.5">Two-Factor Authentication</h2>
      {twoFactorError && (
        <div className="mb-2 p-2 bg-nurturing-light border-[0.5px] border-nurturing text-safe text-xs">
          {twoFactorError}
        </div>
      )}

      {showRecoveryCodes && recoveryCodes && (
        <div className="mb-4 p-3 bg-white border border-[0.5px] border-safe/30">
          <h3 className="text-sm font-semibold text-safe mb-2">Recovery Codes</h3>
          <p className="text-xs text-safe-light mb-2">
            Save these codes in a safe place. You can use them to access your account if you lose access to your authenticator app.
          </p>
          <div className="grid grid-cols-2 gap-2 mb-2">
            {recoveryCodes.map((code, idx) => (
              <div key={idx} className="p-2 bg-white border border-[0.5px] border-safe/20 font-mono text-xs text-safe">
                {code}
              </div>
            ))}
          </div>
          <button
            onClick={() => setShowRecoveryCodes(false)}
            className="text-xs text-natural hover:underline"
          >
            I've saved these codes
          </button>
        </div>
      )}

      {!is2FAEnabled && !twoFactorSetup && (
        <div className="space-y-2">
          <SettingsRow label="Status" description="Two-factor authentication is currently disabled.">
            <span className="text-sm text-safe-light">Disabled</span>
          </SettingsRow>
          <button
            onClick={handleSetup2FA}
            disabled={twoFactorSettingUp}
            className="px-2 py-1 text-sm bg-natural hover:bg-natural-dark text-white rounded-none transition-colors disabled:opacity-50 flex items-center gap-1"
          >
            {twoFactorSettingUp && <LoadingSpinner size="sm" color="white" />}
            Enable Two-Factor Authentication
          </button>
        </div>
      )}

      {!is2FAEnabled && twoFactorSetup && (
        <div className="space-y-3 p-3 bg-white border border-[0.5px] border-safe/30">
          <h3 className="text-sm font-semibold text-safe">Setup Two-Factor Authentication</h3>
          <p className="text-xs text-safe-light">
            1. Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
          </p>
          <div className="flex justify-center py-2">
            <QRCode url={twoFactorSetup.qr_code_url} size={200} />
          </div>
          <p className="text-xs text-safe-light">
            2. Or enter this code manually: <code className="font-mono bg-safe-light/10 px-1">{twoFactorSetup.manual_entry_key}</code>
          </p>
          <p className="text-xs text-safe-light">
            3. Enter the 6-digit code from your app to verify:
          </p>
          <form onSubmit={handleVerify2FA} className="space-y-2">
            <FormField
              label="Verification code"
              name="twoFactorCode"
              type="text"
              value={twoFactorCode}
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, '').slice(0, 6)
                setTwoFactorCode(value)
                setTwoFactorError(null)
              }}
              error={twoFactorError || undefined}
              compact
              placeholder="000000"
              maxLength={6}
            />
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={twoFactorVerifying || twoFactorCode.length !== 6}
                className="px-2 py-1 text-sm bg-natural hover:bg-natural-dark text-white rounded-none transition-colors disabled:opacity-50 flex items-center gap-1"
              >
                {twoFactorVerifying && <LoadingSpinner size="sm" color="white" />}
                Verify and Enable
              </button>
              <button
                type="button"
                onClick={cancel2FASetup}
                disabled={twoFactorVerifying}
                className="px-2 py-1 text-sm border border-[0.5px] border-safe/30 text-safe hover:bg-safe-light/10 rounded-none transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {is2FAEnabled && (
        <div className="space-y-2">
          <SettingsRow label="Status" description="Two-factor authentication is enabled for your account.">
            <span className="text-sm text-natural">Enabled</span>
          </SettingsRow>
          <button
            onClick={handleDisable2FA}
            disabled={twoFactorDisabling}
            className="px-2 py-1 text-sm bg-nurturing hover:bg-nurturing-dark text-white rounded-none transition-colors disabled:opacity-50 flex items-center gap-1"
          >
            {twoFactorDisabling && <LoadingSpinner size="sm" color="white" />}
            Disable Two-Factor Authentication
          </button>
        </div>
      )}

      <div className="mt-4 pt-2 border-t border-safe/20">
        <Link to="/audit" className="text-xs text-natural hover:underline">
          View login history →
        </Link>
      </div>
    </div>
  )
}

function NotificationsTab({
  emailNotifications,
  setEmailNotifications,
  assignmentAlerts,
  setAssignmentAlerts,
  sessionReminders,
  setSessionReminders,
  weeklyDigest,
  setWeeklyDigest,
  saving,
  onSave,
}: {
  emailNotifications: boolean
  setEmailNotifications: (v: boolean) => void
  assignmentAlerts: boolean
  setAssignmentAlerts: (v: boolean) => void
  sessionReminders: boolean
  setSessionReminders: (v: boolean) => void
  weeklyDigest: boolean
  setWeeklyDigest: (v: boolean) => void
  saving: boolean
  onSave: () => void
}) {
  return (
    <div className="space-y-0">
      <h2 className="text-sm font-semibold text-safe mb-1.5">Email</h2>
      <SettingsRow label="Email notifications" description="General updates and alerts.">
        <Switch checked={emailNotifications} onChange={setEmailNotifications} ariaLabel="Email notifications" />
      </SettingsRow>
      <SettingsRow label="Assignment alerts" description="When you are assigned to a service.">
        <Switch checked={assignmentAlerts} onChange={setAssignmentAlerts} ariaLabel="Assignment alerts" />
      </SettingsRow>
      <SettingsRow label="Session reminders" description="Reminders before scheduled sessions.">
        <Switch checked={sessionReminders} onChange={setSessionReminders} ariaLabel="Session reminders" />
      </SettingsRow>
      <SettingsRow label="Weekly digest" description="Summary of activity each week.">
        <Switch checked={weeklyDigest} onChange={setWeeklyDigest} ariaLabel="Weekly digest" />
      </SettingsRow>
      <div className="pt-2">
        <button
          onClick={onSave}
          disabled={saving}
          className="px-2 py-1 text-sm bg-natural hover:bg-natural-dark text-white rounded-none transition-colors disabled:opacity-50 flex items-center gap-1"
        >
          {saving && <LoadingSpinner size="sm" color="white" />}
          Save
        </button>
      </div>
    </div>
  )
}

function AboutTab() {
  return (
    <div className="space-y-0">
      <h2 className="text-sm font-semibold text-safe mb-1.5">Evexía</h2>
      <SettingsRow label="Version">
        <span className="text-xs text-safe-light">1.0.0</span>
      </SettingsRow>
      <SettingsRow label="Platform" description="Service management and delivery.">
        <span className="text-xs text-safe-light">Evexía</span>
      </SettingsRow>
      <div className="mt-2 pt-2 border-t border-safe/20 flex flex-wrap gap-2">
        <span className="text-xs text-safe-light">License</span>
        <span className="text-xs text-safe-light">·</span>
        <span className="text-xs text-safe-light">Privacy</span>
      </div>
    </div>
  )
}
