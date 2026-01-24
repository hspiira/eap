/**
 * Settings Page
 * Tabbed: Account, Industries, Users, Client tags, Contacts, Preferences, Security, Notifications, About.
 * Industries, Users, and Client tags have embedded list UIs with create modals. URL-based tabs, max-w-7xl.
 */

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Breadcrumb } from '@/components/common/Breadcrumb'
import { FormField } from '@/components/common/FormField'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/contexts/ToastContext'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { IndustriesTab } from '@/routes/settings/-IndustriesTab'
import { UsersTab } from '@/routes/settings/-UsersTab'
import { ClientTagsTab } from '@/routes/settings/-ClientTagsTab'
import {
  User,
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
  { id: 'account', label: 'Account', icon: User },
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
  const { isAuthenticated, isLoading: authLoading, logout } = useAuth()
  const { showSuccess, showError } = useToast()

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

  const savePreferences = () => {
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
  }

  const handleSecuritySubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const err: Record<string, string> = {}
    if (!currentPassword) err.currentPassword = 'Required'
    if (!newPassword) err.newPassword = 'Required'
    else if (newPassword.length < 8) err.newPassword = 'Min 8 characters'
    if (newPassword !== confirmPassword) err.confirmPassword = 'Must match'
    setSecurityErrors(err)
    if (Object.keys(err).length > 0) return
    setSecuritySaving(true)
    try {
      showError('Change password not yet available')
    } catch {
      showError('Failed to update password')
    } finally {
      setSecuritySaving(false)
    }
  }

  const saveNotifications = () => {
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
  }

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-calm flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <Breadcrumb items={[{ label: 'Settings' }]} className="mb-2" />
        <h1 className="text-xl font-bold text-safe mb-4">Settings</h1>

        <div className="border-b border-safe mb-4">
          <nav className="flex gap-1" aria-label="Settings tabs">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`flex items-center gap-2 px-3 py-2.5 text-sm font-medium border-b-2 transition-colors rounded-none ${
                  tab === id
                    ? 'border-natural text-natural'
                    : 'border-transparent text-safe hover:text-natural hover:border-safe'
                }`}
              >
                <Icon size={18} />
                {label}
              </button>
            ))}
          </nav>
        </div>

        <div className="bg-calm border border-[0.5px] border-safe p-4">
          {tab === 'account' && <AccountTab onLogout={logout} />}
          {tab === 'industries' && <IndustriesTab />}
          {tab === 'users' && <UsersTab />}
          {tab === 'client-tags' && <ClientTagsTab />}
          {tab === 'contacts' && <ManageLinkTab label="Contacts" path="/contacts" description="Contact records across clients." />}
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
        checked ? 'bg-natural border-natural' : 'bg-calm border-safe'
      }`}
      style={{ borderRadius: '9999px' }}
    >
      <span
        className={`absolute top-0.5 block h-4 w-4 !rounded-full bg-white border border-safe transition-transform ${
          checked ? 'left-[18px]' : 'left-0.5'
        }`}
        style={{ borderRadius: '9999px' }}
      />
    </button>
  )
}

function AccountTab({ onLogout }: { onLogout: () => void }) {
  return (
    <div className="space-y-0">
      <h2 className="text-sm font-semibold text-safe mb-1.5">Session</h2>
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
          className="inline-flex items-center gap-1 px-2 py-1 text-sm border border-[0.5px] border-safe text-safe hover:bg-safe-light/10 rounded-none transition-colors"
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

function CompactSelect({
  label,
  value,
  onChange,
  options,
  className = '',
}: {
  label: string
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
  className?: string
}) {
  return (
    <div className={`py-1 border-b border-safe/20 ${className}`}>
      <label className="block text-xs font-medium text-safe mb-0.5">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full max-w-xs px-2 py-1 text-sm bg-calm border-[0.5px] border-safe rounded-none focus:outline-none focus:border-natural"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
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
      <CompactSelect label="Language" value={language} onChange={setLanguage} options={langOpts} />
      <CompactSelect label="Timezone" value={timezone} onChange={setTimezone} options={tzOpts} />
      <CompactSelect label="Date format" value={dateFormat} onChange={setDateFormat} options={dateOpts} />
      <CompactSelect label="Week starts on" value={weekStartsOn} onChange={setWeekStartsOn} options={weekOpts} />
      <h2 className="text-sm font-semibold text-safe mt-2 mb-1.5">Security</h2>
      <CompactSelect label="Session timeout" value={sessionTimeout} onChange={setSessionTimeout} options={timeoutOpts} />
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
}) {
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
      <p className="text-xs text-safe-light mt-2">Two-factor authentication can be enabled from your user profile when available.</p>
      <div className="mt-2 pt-2 border-t border-safe/20">
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
