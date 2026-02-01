/**
 * Client Detail Page
 * Tabs: Overview (summary, stats, events), People, Contracts, Reports
 */

import { createFileRoute, useNavigate, Link } from '@tanstack/react-router'
import { useState, useEffect, useCallback } from 'react'
import { useModal } from '@/hooks/useModal'
import { AppLayout } from '@/components/layout/AppLayout'
import { Breadcrumb } from '@/components/common/Breadcrumb'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LifecycleActions } from '@/components/common/LifecycleActions'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { DataTable, type Column } from '@/components/common/DataTable'
import { EmptyState } from '@/components/common/EmptyState'
import { useToast } from '@/contexts/ToastContext'
import { useAuth } from '@/contexts/AuthContext'
import { clientsApi } from '@/api/endpoints/clients'
import { clientTagsApi } from '@/api/endpoints/client-tags'
import { contactsApi } from '@/api/endpoints/contacts'
import { personsApi } from '@/api/endpoints/persons'
import { contractsApi } from '@/api/endpoints/contracts'
import { activitiesApi } from '@/api/endpoints/activities'
import { industriesApi } from '@/api/endpoints/industries'
import { serviceSessionsApi } from '@/api/endpoints/service-sessions'
import { CreateModal } from '@/components/common/CreateModal'
import { ConfirmationModal } from '@/components/common/ConfirmationModal'
import { CreateActivityForm } from '@/components/forms/CreateActivityForm'
import { CreateContactForm } from '@/components/forms/CreateContactForm'
import { CreateContractForm } from '@/components/forms/CreateContractForm'
import { CreatePersonModal } from '@/components/forms/CreatePersonModal'
import { EditClientForm } from '@/components/forms/EditClientForm'
import type { Client, ClientTag, Contact, Person, Contract, Activity, ServiceSession } from '@/types/entities'
import type { BaseStatus, ContractStatus } from '@/types/enums'
import type { SessionStatus } from '@/types/enums'
import {
  Edit,
  Building2,
  MapPin,
  Phone,
  Mail,
  Tag,
  Plus,
  X,
  Users,
  FileText,
  BarChart3,
  LayoutDashboard,
  Activity as ActivityIcon,
  UserCircle,
  Calendar,
  Star,
  CheckCircle,
} from 'lucide-react'

const TABS = [
  { id: 'overview' as const, label: 'Overview', icon: LayoutDashboard },
  { id: 'people' as const, label: 'People', icon: Users },
  { id: 'contacts' as const, label: 'Contacts', icon: UserCircle },
  { id: 'contracts' as const, label: 'Contracts', icon: FileText },
  { id: 'sessions' as const, label: 'Sessions', icon: Calendar },
  { id: 'reports' as const, label: 'Reports', icon: BarChart3 },
] as const

type TabId = (typeof TABS)[number]['id']

export const Route = createFileRoute('/clients/$clientId')({
  validateSearch: (search: Record<string, unknown>) => ({
    tab: (
      ['overview', 'people', 'contacts', 'contracts', 'sessions', 'reports'] as const
    ).includes(search?.tab as TabId)
      ? (search.tab as TabId)
      : 'overview',
  }),
  component: ClientDetailPage,
})

function ClientDetailPage() {
  const { clientId } = Route.useParams()
  const { tab } = Route.useSearch()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const { user_id } = useAuth()

  const [client, setClient] = useState<Client | null>(null)
  const [tags, setTags] = useState<ClientTag[]>([])
  const [allTags, setAllTags] = useState<ClientTag[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [tagAssignLoading, setTagAssignLoading] = useState(false)
  const [tagUnassignId, setTagUnassignId] = useState<string | null>(null)
  const [addTagId, setAddTagId] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  const [people, setPeople] = useState<Person[]>([])
  const [peopleLoading, setPeopleLoading] = useState(false)
  const [peopleError, setPeopleError] = useState<string | null>(null)

  const [contracts, setContracts] = useState<Contract[]>([])
  const [contractsLoading, setContractsLoading] = useState(false)
  const [contractsError, setContractsError] = useState<string | null>(null)

  const [activities, setActivities] = useState<Activity[]>([])
  const [activitiesLoading, setActivitiesLoading] = useState(false)

  const [contacts, setContacts] = useState<Contact[]>([])
  const [contactsLoading, setContactsLoading] = useState(false)
  const [contactsError, setContactsError] = useState<string | null>(null)
  const [primaryContact, setPrimaryContact] = useState<Contact | null>(null)

  const [industryName, setIndustryName] = useState<string | null>(null)
  const [sessions, setSessions] = useState<ServiceSession[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [sessionsError, setSessionsError] = useState<string | null>(null)
  const [clientStats, setClientStats] = useState<{ child_count?: number; contract_count?: number; is_verified?: boolean } | null>(null)
  const [childClients, setChildClients] = useState<Client[]>([])
  const [childClientsLoading, setChildClientsLoading] = useState(false)
  const [lifecycleReasonAction, setLifecycleReasonAction] = useState<'suspend' | 'terminate' | null>(null)

  const activityModal = useModal()
  const contactModal = useModal()
  const contractModal = useModal()
  const [createPersonModalOpen, setCreatePersonModalOpen] = useState(false)
  const editClientModal = useModal()

  const fetchClient = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await clientsApi.getById(clientId)
      setClient(data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load client'
      setError(msg)
      showError(msg)
    } finally {
      setLoading(false)
    }
  }, [clientId, showError])

  useEffect(() => {
    fetchClient()
  }, [fetchClient])

  const fetchStats = useCallback(async () => {
    if (!clientId) return
    try {
      const stats = await clientsApi.getStats(clientId)
      setClientStats(stats)
    } catch {
      setClientStats(null)
    }
  }, [clientId])

  const fetchChildClients = useCallback(async () => {
    if (!clientId) return
    try {
      setChildClientsLoading(true)
      const res = await clientsApi.getChildren(clientId, { limit: 50 })
      setChildClients(res.items ?? [])
    } catch {
      setChildClients([])
    } finally {
      setChildClientsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    if (clientId) fetchStats()
  }, [clientId, fetchStats])

  useEffect(() => {
    if (client?.id && clientStats?.child_count && clientStats.child_count > 0) {
      fetchChildClients()
    } else {
      setChildClients([])
    }
  }, [client?.id, clientStats?.child_count, fetchChildClients])

  useEffect(() => {
    if (!clientId) return
    const loadTags = async () => {
      try {
        const [clientTags, list] = await Promise.all([
          clientsApi.getTags(clientId).catch(() => []),
          clientTagsApi.list({ limit: 200 }).catch(() => ({ items: [] })),
        ])
        setTags(Array.isArray(clientTags) ? clientTags : [])
        setAllTags(Array.isArray(list?.items) ? list.items : [])
      } catch (err) {
        console.error('Error fetching tags:', err)
      }
    }
    loadTags()
  }, [clientId])

  const fetchPeople = useCallback(async () => {
    if (!clientId) return
    try {
      setPeopleLoading(true)
      setPeopleError(null)
      const res = await personsApi.list({
        client_id: clientId,
        limit: 200,
      } as Record<string, unknown>)
      const filtered = (res.items || []).filter((p) =>
        ['ClientEmployee', 'Dependent'].includes(p.person_type)
      )
      setPeople(filtered)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load people'
      setPeopleError(msg)
    } finally {
      setPeopleLoading(false)
    }
  }, [clientId])

  const fetchContracts = useCallback(async () => {
    if (!clientId) return
    try {
      setContractsLoading(true)
      setContractsError(null)
      const res = await contractsApi.list({
        client_id: clientId,
        limit: 200,
      } as Record<string, unknown>)
      const items = (res.items || []).filter((c) => c.client_id === clientId)
      setContracts(items)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load contracts'
      setContractsError(msg)
    } finally {
      setContractsLoading(false)
    }
  }, [clientId])

  const fetchActivities = useCallback(async () => {
    if (!clientId) return
    try {
      setActivitiesLoading(true)
      const res = await activitiesApi.list({
        client_id: clientId,
        limit: 10,
        sort_by: 'occurred_at',
        sort_desc: true,
      } as Record<string, unknown>)
      setActivities(res.items || [])
    } catch (err) {
      console.error('Error fetching activities:', err)
    } finally {
      setActivitiesLoading(false)
    }
  }, [clientId])

  const fetchContacts = useCallback(async () => {
    if (!clientId) return
    try {
      setContactsLoading(true)
      setContactsError(null)
      const [listRes, primary] = await Promise.all([
        contactsApi.list({ client_id: clientId, limit: 200 } as Record<string, unknown>),
        contactsApi.getPrimaryForClient(clientId).catch(() => null),
      ])
      setContacts(listRes?.items ?? [])
      setPrimaryContact(primary ?? null)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load contacts'
      setContactsError(msg)
    } finally {
      setContactsLoading(false)
    }
  }, [clientId])

  const fetchSessions = useCallback(async () => {
    if (!clientId || contracts.length === 0) {
      setSessions([])
      return
    }
    try {
      setSessionsLoading(true)
      setSessionsError(null)
      const contractIds = contracts.map((c) => c.id)
      const res = await serviceSessionsApi.list({
        limit: 100,
        sort_by: 'scheduled_at',
        sort_desc: true,
      } as Record<string, unknown>)
      const filtered = (res.items || []).filter(
        (s) => s.contract_id && contractIds.includes(s.contract_id)
      )
      setSessions(filtered)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load sessions'
      setSessionsError(msg)
      console.error('Error fetching sessions:', err)
    } finally {
      setSessionsLoading(false)
    }
  }, [clientId, contracts])

  useEffect(() => {
    if (tab === 'people') fetchPeople()
  }, [tab, fetchPeople])

  useEffect(() => {
    if (tab === 'contracts') fetchContracts()
  }, [tab, fetchContracts])

  useEffect(() => {
    if (tab === 'contacts') fetchContacts()
  }, [tab, fetchContacts])

  useEffect(() => {
    if (tab === 'overview') {
      fetchActivities()
      fetchPeople()
      fetchContracts()
      fetchContacts()
    }
  }, [tab, fetchActivities, fetchPeople, fetchContracts, fetchContacts])

  useEffect(() => {
    if (tab === 'sessions') {
      fetchContracts()
    }
  }, [tab, fetchContracts])

  useEffect(() => {
    if (client?.industry_id) {
      industriesApi
        .getById(client.industry_id)
        .then((ind) => setIndustryName(ind.name))
        .catch(() => setIndustryName(null))
    } else {
      setIndustryName(null)
    }
  }, [client?.industry_id])

  useEffect(() => {
    if ((tab === 'overview' || tab === 'sessions') && contracts.length > 0) fetchSessions()
    else if (tab !== 'overview' && tab !== 'sessions') {
      setSessions([])
      setSessionsError(null)
    }
  }, [tab, contracts.length, fetchSessions])

  const handleAssignTag = async () => {
    if (!addTagId) return
    try {
      setTagAssignLoading(true)
      await clientTagsApi.assign(addTagId, clientId)
      const tag = allTags.find((t) => t.id === addTagId)
      if (tag) setTags((prev) => [...prev, tag])
      setAddTagId('')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to assign tag'
      showError(msg)
    } finally {
      setTagAssignLoading(false)
    }
  }

  const handleUnassignTag = async (tagId: string) => {
    try {
      setTagUnassignId(tagId)
      await clientTagsApi.unassign(tagId, clientId)
      setTags((prev) => prev.filter((t) => t.id !== tagId))
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to remove tag'
      showError(msg)
    } finally {
      setTagUnassignId(null)
    }
  }

  const assignableTags = allTags.filter((t) => !tags.some((a) => a.id === t.id))
  const addTagOptions = [
    { value: '', label: 'Select tag to add' },
    ...assignableTags.map((t) => ({
      value: t.id,
      label: t.color ? `${t.name} (${t.color})` : t.name,
    })),
  ]

  const handleAction = async (action: string) => {
    if (!clientId) return
    try {
      setActionLoading(true)
      switch (action) {
        case 'verify':
          if (!user_id) {
            showError('You must be signed in to verify a client')
            setActionLoading(false)
            return
          }
          await clientsApi.verify(clientId, user_id)
          showSuccess('Client marked as verified')
          break
        case 'activate':
          await clientsApi.activate(clientId)
          showSuccess('Client activated')
          break
        case 'deactivate':
          await clientsApi.deactivate(clientId)
          showSuccess('Client deactivated')
          break
        case 'archive':
          await clientsApi.archive(clientId)
          showSuccess('Client archived')
          break
        case 'restore':
        case 'unarchive':
          await clientsApi.restore(clientId)
          showSuccess('Client restored')
          break
        case 'suspend':
        case 'terminate':
          setLifecycleReasonAction(action as 'suspend' | 'terminate')
          setActionLoading(false)
          return
        default:
          showSuccess(`Client ${action} action initiated`)
      }
      await fetchClient()
      await fetchStats()
    } catch (err: unknown) {
      showError(err instanceof Error ? err.message : `Failed to ${action} client`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleLifecycleReasonConfirm = async (reason: string) => {
    if (!clientId || !lifecycleReasonAction || !reason.trim()) return
    const action = lifecycleReasonAction
    try {
      setActionLoading(true)
      if (action === 'suspend') {
        await clientsApi.suspend(clientId, reason.trim())
        showSuccess('Client suspended')
      } else {
        await clientsApi.terminate(clientId, reason.trim())
        showSuccess('Client terminated')
      }
      setLifecycleReasonAction(null)
      await fetchClient()
      await fetchStats()
    } catch (err: unknown) {
      showError(err instanceof Error ? err.message : `Failed to ${action} client`)
    } finally {
      setActionLoading(false)
    }
  }

  const setTab = (t: TabId) => {
    navigate({ to: '.', search: { tab: t } })
  }

  const handleActivityCreated = () => {
    activityModal.close()
    fetchActivities()
  }

  const handleContactCreated = () => {
    contactModal.close()
    fetchContacts()
  }

  const handleContractCreated = () => {
    contractModal.close()
    fetchContracts()
  }

  const handleClientUpdated = () => {
    editClientModal.close()
    fetchClient()
  }

  if (loading) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </AppLayout>
    )
  }

  if (error || !client) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error || 'Client not found'}
            onRetry={fetchClient}
          />
        </div>
      </AppLayout>
    )
  }

  const breadcrumbItems = [
    { label: 'Clients', href: '/clients' },
    { label: client.name },
  ]

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <Breadcrumb items={breadcrumbItems} className="mb-2" />

        <div className="flex items-center gap-2 flex-wrap mb-4">
          <div className="flex items-center gap-2 min-w-0">
            <h1 className="text-xl font-bold text-text truncate">{client.name}</h1>
            {client.is_verified && (
              <span
                className="flex items-center justify-center flex-shrink-0 w-6 h-6 bg-primary/15 border border-[0.5px] border-primary/40 text-primary rounded-none"
                title="Verified"
              >
                <CheckCircle size={14} strokeWidth={2.5} aria-hidden="true" />
                <span className="sr-only">Verified</span>
              </span>
            )}
            {client.status?.toLowerCase() === 'active' && (
              <span className="flex items-center flex-shrink-0" title="Active">
                <span
                  className="status-blink-dot flex-shrink-0 w-2.5 h-2.5 rounded-full bg-primary"
                  aria-hidden="true"
                />
                <span className="sr-only">Active</span>
              </span>
            )}
          </div>
          <button
            onClick={() => editClientModal.open()}
            className="p-1.5 text-text hover:text-primary hover:bg-surface-hover rounded-none transition-colors flex-shrink-0"
            aria-label="Edit client"
          >
            <Edit size={18} />
          </button>
          {client.status?.toLowerCase() !== 'active' && (
            <StatusBadge status={client.status as BaseStatus} />
          )}
          {!client.is_verified && (
            <button
              type="button"
              onClick={() => handleAction('verify')}
              disabled={actionLoading || !user_id}
              className="flex items-center justify-center p-1.5 border border-[0.5px] border-border rounded-none bg-neutral hover:bg-neutral-dark text-white transition-colors disabled:opacity-50"
              title={!user_id ? 'You must be signed in to verify' : 'Verify client'}
              aria-label="Verify client"
            >
              <CheckCircle size={14} />
            </button>
          )}
          <LifecycleActions
            currentStatus={client.status}
            onAction={handleAction}
            loading={actionLoading}
          />
        </div>

        {/* Tabs */}
        <div className="border-b border-border mb-4">
          <nav className="flex" aria-label="Client sections">
            {TABS.map(({ id, label, icon: Icon }) => {
              const count =
                id === 'people'
                  ? people.length
                  : id === 'contacts'
                    ? contacts.length
                    : id === 'contracts'
                      ? contracts.length
                      : id === 'sessions'
                        ? sessions.length
                        : null
              return (
                <button
                  key={id}
                  onClick={() => setTab(id)}
                  className={`flex items-center gap-2 px-3 py-2.5 text-sm font-medium transition-colors rounded-none ${
                    tab === id
                      ? 'bg-calm-dark text-primary'
                      : 'text-text hover:bg-calm hover:text-primary'
                  }`}
                >
                  <Icon size={18} />
                  {label}
                  {count !== null && (
                    <span className="text-text-muted font-normal">({count})</span>
                  )}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab content */}
        {tab === 'overview' && (
          <OverviewTab
            client={client}
            tags={tags}
            assignableTags={assignableTags}
            addTagId={addTagId}
            setAddTagId={setAddTagId}
            addTagOptions={addTagOptions}
            tagAssignLoading={tagAssignLoading}
            tagUnassignId={tagUnassignId}
            onAssignTag={handleAssignTag}
            onUnassignTag={handleUnassignTag}
            onTagClick={(tagId) => navigate({ to: `/client-tags/${tagId}` })}
            peopleCount={people.length}
            contactsCount={contacts.length}
            contractsCount={contracts.length}
            clientStats={clientStats}
            childClients={childClients}
            childClientsLoading={childClientsLoading}
            activities={activities}
            activitiesLoading={activitiesLoading}
            primaryContact={primaryContact}
            industryName={industryName}
            sessions={sessions}
            sessionsLoading={sessionsLoading}
            hasContracts={contracts.length > 0}
            onLogActivity={() => activityModal.open()}
            onViewActivity={(id) => navigate({ to: `/activities/${id}` })}
            onViewAllActivities={() => navigate({ to: '/activities' })}
            onViewClient={(id) => navigate({ to: `/clients/${id}` })}
          />
        )}

        {tab === 'people' && (
          <PeopleTab
            people={people}
            loading={peopleLoading}
            error={peopleError}
            onRetry={fetchPeople}
            onRowClick={(p) => navigate({ to: `/persons/${p.id}` })}
            onAddPerson={() => setCreatePersonModalOpen(true)}
          />
        )}

        {tab === 'contacts' && (
          <ContactsTab
            contacts={contacts}
            loading={contactsLoading}
            error={contactsError}
            onRetry={fetchContacts}
            onRowClick={(c) => navigate({ to: '/settings/contacts/$contactId', params: { contactId: c.id } })}
            onAddContact={() => contactModal.open()}
          />
        )}

        {tab === 'contracts' && (
          <ContractsTab
            contracts={contracts}
            loading={contractsLoading}
            error={contractsError}
            onRetry={fetchContracts}
            onRowClick={(c) => navigate({ to: `/contracts/${c.id}` })}
            onAddContract={() => contractModal.open()}
          />
        )}

        {tab === 'sessions' && (
          <SessionsTab
            sessions={sessions}
            loading={sessionsLoading}
            error={sessionsError}
            onRetry={fetchSessions}
            onRowClick={(s) => navigate({ to: '/sessions/$sessionId', params: { sessionId: s.id } })}
          />
        )}

        {tab === 'reports' && (
          <EmptyState
            title="Reports"
            message="Reports for this client will be available here. Coming soon."
            icon={BarChart3}
            variant="no-data"
          />
        )}

        <CreateModal
          isOpen={activityModal.isOpen}
          onClose={activityModal.close}
          title="Log activity"
          loading={activityModal.loading}
        >
          <CreateActivityForm
            initialClientId={clientId}
            onSuccess={handleActivityCreated}
            onCancel={activityModal.close}
            onLoadingChange={activityModal.setLoading}
          />
        </CreateModal>

        <CreateModal
          isOpen={contactModal.isOpen}
          onClose={contactModal.close}
          title="Add contact"
          loading={contactModal.loading}
        >
          <CreateContactForm
            initialClientId={clientId}
            onSuccess={handleContactCreated}
            onCancel={contactModal.close}
            onLoadingChange={contactModal.setLoading}
          />
        </CreateModal>

        <CreateModal
          isOpen={contractModal.isOpen}
          onClose={contractModal.close}
          title="Add contract"
          loading={contractModal.loading}
        >
          <CreateContractForm
            initialClientId={clientId}
            onSuccess={handleContractCreated}
            onCancel={contractModal.close}
            onLoadingChange={contractModal.setLoading}
          />
        </CreateModal>

        <CreatePersonModal
          isOpen={createPersonModalOpen}
          onClose={() => setCreatePersonModalOpen(false)}
          initialClientId={clientId}
          onCreated={() => fetchPeople()}
        />

        <CreateModal
          isOpen={editClientModal.isOpen}
          onClose={editClientModal.close}
          title="Edit client"
          loading={editClientModal.loading}
        >
          <EditClientForm
            client={client}
            onSuccess={handleClientUpdated}
            onCancel={editClientModal.close}
            onLoadingChange={editClientModal.setLoading}
          />
        </CreateModal>

        <ConfirmationModal
          isOpen={!!lifecycleReasonAction}
          onClose={() => setLifecycleReasonAction(null)}
          onConfirm={(reason) => { if (reason !== undefined) void handleLifecycleReasonConfirm(reason) }}
          title={lifecycleReasonAction === 'suspend' ? 'Suspend client' : 'Terminate client'}
          message={
            lifecycleReasonAction === 'suspend'
              ? 'A reason is required to suspend this client.'
              : 'A reason is required to terminate this client. This action is permanent.'
          }
          requireReason
          reasonPlaceholder="Enter reason..."
          loading={actionLoading}
          confirmLabel="Confirm"
          cancelLabel="Cancel"
          variant="warning"
        />
      </div>
    </AppLayout>
  )
}

function OverviewTab({
  client,
  tags,
  assignableTags,
  addTagId,
  setAddTagId,
  addTagOptions,
  tagAssignLoading,
  tagUnassignId,
  onAssignTag,
  onUnassignTag,
  onTagClick,
  peopleCount,
  contactsCount,
  contractsCount,
  clientStats,
  childClients,
  childClientsLoading,
  activities,
  activitiesLoading,
  primaryContact,
  industryName,
  sessions,
  sessionsLoading,
  hasContracts,
  onLogActivity,
  onViewActivity,
  onViewAllActivities,
  onViewClient,
}: {
  client: Client
  tags: ClientTag[]
  assignableTags: ClientTag[]
  addTagId: string
  setAddTagId: (v: string) => void
  addTagOptions: { value: string; label: string }[]
  tagAssignLoading: boolean
  tagUnassignId: string | null
  onAssignTag: () => void
  onUnassignTag: (id: string) => void
  onTagClick: (id: string) => void
  peopleCount: number
  contactsCount: number
  contractsCount: number
  clientStats: { child_count?: number; contract_count?: number; is_verified?: boolean } | null
  childClients: Client[]
  childClientsLoading: boolean
  activities: Activity[]
  activitiesLoading: boolean
  primaryContact: Contact | null
  industryName: string | null
  sessions: ServiceSession[]
  sessionsLoading: boolean
  hasContracts: boolean
  onLogActivity: () => void
  onViewActivity: (id: string) => void
  onViewAllActivities: () => void
  onViewClient: (id: string) => void
}) {
  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link
          to="."
          search={{ tab: 'people' }}
          className="bg-surface border border-[0.5px] border-border p-4 hover:border-primary transition-colors block"
        >
          <div className="flex items-center gap-2 text-text mb-1">
            <Users size={20} />
            <span className="text-sm font-medium">People</span>
          </div>
          <p className="text-2xl font-bold text-text">{peopleCount}</p>
          <p className="text-xs text-text-muted">Employees & dependants</p>
        </Link>
        <Link
          to="."
          search={{ tab: 'contacts' }}
          className="bg-surface border border-[0.5px] border-border p-4 hover:border-primary transition-colors block"
        >
          <div className="flex items-center gap-2 text-text mb-1">
            <UserCircle size={20} />
            <span className="text-sm font-medium">Contacts</span>
          </div>
          <p className="text-2xl font-bold text-text">{contactsCount}</p>
        </Link>
        <Link
          to="."
          search={{ tab: 'contracts' }}
          className="bg-surface border border-[0.5px] border-border p-4 hover:border-primary transition-colors block"
        >
          <div className="flex items-center gap-2 text-text mb-1">
            <FileText size={20} />
            <span className="text-sm font-medium">Contracts</span>
          </div>
          <p className="text-2xl font-bold text-text">{clientStats?.contract_count ?? contractsCount}</p>
        </Link>
        {(clientStats?.child_count ?? 0) > 0 && (
          <div className="bg-surface border border-[0.5px] border-border p-4">
            <div className="flex items-center gap-2 text-text mb-1">
              <Building2 size={20} />
              <span className="text-sm font-medium">Child clients</span>
            </div>
            <p className="text-2xl font-bold text-text">{clientStats?.child_count ?? 0}</p>
            <p className="text-xs text-text-muted">Sub-clients</p>
          </div>
        )}
      </div>

      {/* Child clients list (when parent) */}
      {(childClients.length > 0 || childClientsLoading) && (
        <div className="bg-surface border border-[0.5px] border-border p-6">
          <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
            <Building2 size={20} />
            Child clients
          </h2>
          {childClientsLoading ? (
            <div className="flex justify-center py-6">
              <LoadingSpinner size="sm" />
            </div>
          ) : (
            <ul className="space-y-2">
              {childClients.map((c) => (
                <li key={c.id} className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
                  <div>
                    <p className="text-text font-medium">{c.name}</p>
                    {c.code && <p className="text-sm text-text-muted">Code: {c.code}</p>}
                  </div>
                  <button
                    type="button"
                    onClick={() => onViewClient(c.id)}
                    className="text-primary hover:text-primary-hover text-sm font-medium"
                  >
                    View
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Summary + Primary contact + Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <div className="bg-surface border border-[0.5px] border-border p-6">
            <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
              <Building2 size={20} />
              Summary
            </h2>
            <dl className="space-y-2 text-sm">
              <div className="flex gap-2">
                <dt className="text-text-muted w-28">Status</dt>
                <dd>
                  <StatusBadge status={client.status as BaseStatus} size="sm" />
                </dd>
              </div>
              {client.code && (
                <div className="flex gap-2">
                  <dt className="text-text-muted w-28">Code</dt>
                  <dd className="text-text">{client.code}</dd>
                </div>
              )}
              {(industryName || client.industry_id) && (
                <div className="flex gap-2">
                  <dt className="text-text-muted w-28">Industry</dt>
                  <dd className="text-text">{industryName ?? client.industry_id}</dd>
                </div>
              )}
              {client.contact_info?.email && (
                <div className="flex gap-2">
                  <dt className="text-text-muted w-28 flex items-center gap-1">
                    <Mail size={14} /> Email
                  </dt>
                  <dd className="text-text">{client.contact_info.email}</dd>
                </div>
              )}
              {client.contact_info?.phone && (
                <div className="flex gap-2">
                  <dt className="text-text-muted w-28 flex items-center gap-1">
                    <Phone size={14} /> Phone
                  </dt>
                  <dd className="text-text">{client.contact_info.phone}</dd>
                </div>
              )}
              {client.contact_info?.address && (
                <div className="flex gap-2">
                  <dt className="text-text-muted w-28 flex items-center gap-1">
                    <MapPin size={14} /> Contact address
                  </dt>
                  <dd className="text-text">{client.contact_info.address}</dd>
                </div>
              )}
              {client.billing_address && (client.billing_address.city || client.billing_address.country || client.billing_address.street) && (
                <div className="flex gap-2">
                  <dt className="text-text-muted w-28 flex items-center gap-1">
                    <MapPin size={14} /> Billing address
                  </dt>
                  <dd className="text-text">
                    {[client.billing_address.street, client.billing_address.city, client.billing_address.postal_code, client.billing_address.country]
                      .filter(Boolean)
                      .join(', ')}
                  </dd>
                </div>
              )}
              {client.preferred_contact_method && (
                <div className="flex gap-2">
                  <dt className="text-text-muted w-28">Preferred contact</dt>
                  <dd className="text-text capitalize">{client.preferred_contact_method}</dd>
                </div>
              )}
              <div className="flex gap-2">
                <dt className="text-text-muted w-28">Updated</dt>
                <dd className="text-text">
                  {new Date(client.updated_at).toLocaleString()}
                </dd>
              </div>
            </dl>
          </div>

          {primaryContact && (
            <div className="bg-surface border border-[0.5px] border-border p-6">
              <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <Star size={20} className="text-nurturing" />
                Primary contact
              </h2>
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="font-medium text-text">
                    {[primaryContact.first_name, primaryContact.last_name].filter(Boolean).join(' ')}
                  </p>
                  {primaryContact.title && (
                    <p className="text-sm text-text-muted">{primaryContact.title}</p>
                  )}
                  {primaryContact.contact_info?.email && (
                    <p className="text-sm text-text-muted">{primaryContact.contact_info.email}</p>
                  )}
                  {primaryContact.contact_info?.phone && !primaryContact.contact_info?.email && (
                    <p className="text-sm text-text-muted">{primaryContact.contact_info.phone}</p>
                  )}
                </div>
                <Link
                  to="/settings/contacts/$contactId"
                  params={{ contactId: primaryContact.id }}
                  className="text-primary hover:text-primary-hover text-sm font-medium flex-shrink-0"
                >
                  View
                </Link>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="bg-surface border border-[0.5px] border-border p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-text flex items-center gap-2">
                <ActivityIcon size={20} />
                Recent events
              </h2>
              <button
                onClick={onLogActivity}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-primary hover:bg-primary-hover text-white rounded-none transition-colors"
              >
                <Plus size={16} />
                Log activity
              </button>
            </div>
            {activitiesLoading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="md" />
              </div>
            ) : activities.length === 0 ? (
              <div>
                <p className="text-text-muted text-sm">No recent activity.</p>
                <button
                  onClick={onLogActivity}
                  className="mt-2 text-primary hover:text-primary-hover text-sm font-medium"
                >
                  Log first activity
                </button>
              </div>
            ) : (
              <>
                <ul className="space-y-3">
                  {activities.map((a) => (
                    <li
                      key={a.id}
                      className="flex items-start gap-2 py-2 border-b border-border/50 last:border-0"
                    >
                      <span className="text-text-muted text-xs uppercase font-medium mt-0.5">
                        {a.activity_type}
                      </span>
                      <div className="flex-1 min-w-0">
                        {a.title && (
                          <p className="text-text font-medium truncate">{a.title}</p>
                        )}
                        {a.description && (
                          <p className="text-text-muted text-sm truncate">{a.description}</p>
                        )}
                        <p className="text-text-muted text-xs mt-1">
                          {new Date(a.occurred_at).toLocaleString()}
                        </p>
                      </div>
                      <button
                        onClick={() => onViewActivity(a.id)}
                        className="text-primary hover:text-primary-hover text-sm font-medium flex-shrink-0"
                      >
                        View
                      </button>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={onViewAllActivities}
                  className="mt-3 text-primary hover:text-primary-hover text-sm font-medium"
                >
                  View all activities
                </button>
              </>
            )}
          </div>

          {hasContracts && (
            <div className="bg-surface border border-[0.5px] border-border p-6">
              <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <Calendar size={20} />
                Upcoming sessions
              </h2>
              {sessionsLoading ? (
                <div className="flex justify-center py-6">
                  <LoadingSpinner size="sm" />
                </div>
              ) : (() => {
                const upcoming = sessions.filter(
                  (s) => new Date(s.scheduled_at) >= new Date()
                ).slice(0, 5)
                return upcoming.length === 0 ? (
                  <p className="text-text-muted text-sm">No upcoming sessions.</p>
                ) : (
                <ul className="space-y-2">
                  {upcoming.map((s) => (
                    <li
                      key={s.id}
                      className="flex items-center justify-between py-2 border-b border-border/50 last:border-0"
                    >
                      <div>
                        <p className="text-text font-medium">
                          {new Date(s.scheduled_at).toLocaleString()}
                        </p>
                        {s.location && (
                          <p className="text-sm text-text-muted">{s.location}</p>
                        )}
                      </div>
                      <Link
                        to="/sessions/$sessionId"
                        params={{ sessionId: s.id }}
                        className="text-primary hover:text-primary-hover text-sm font-medium"
                      >
                        View
                      </Link>
                    </li>
                  ))}
                </ul>
                )
              })()}
            </div>
          )}
        </div>
      </div>

      {/* Tags */}
      <div className="bg-surface border border-[0.5px] border-border p-6">
        <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
          <Tag size={20} />
          Tags
        </h2>
        {tags.length > 0 && (
          <ul className="space-y-2 mb-4">
            {tags.map((t) => (
              <li
                key={t.id}
                className="flex items-center justify-between py-2 px-3 rounded-none hover:bg-surface-hover group"
              >
                <button
                  onClick={() => onTagClick(t.id)}
                  className="flex items-center gap-2 text-left text-primary hover:text-primary-hover font-medium"
                >
                  <span
                    className="w-3 h-3 flex-shrink-0 rounded-none"
                    style={{ backgroundColor: t.color ?? '#8BA88B' }}
                    aria-hidden
                  />
                  <Tag size={14} />
                  {t.name}
                </button>
                <button
                  onClick={() => onUnassignTag(t.id)}
                  disabled={tagUnassignId === t.id}
                  className="p-1 text-nurturing hover:text-nurturing-dark opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50"
                  aria-label={`Remove tag ${t.name}`}
                >
                  <X size={16} />
                </button>
              </li>
            ))}
          </ul>
        )}
        {tags.length === 0 && (
          <p className="text-text-muted text-sm mb-4">No tags assigned.</p>
        )}
        {assignableTags.length > 0 && (
          <div className="flex flex-wrap gap-2 items-end">
            <div className="flex-1 min-w-[200px]">
              <label htmlFor="addTag" className="block text-sm font-medium text-text-muted mb-1">
                Add tag
              </label>
              <select
                id="addTag"
                value={addTagId}
                onChange={(e) => setAddTagId(e.target.value)}
                className="w-full px-4 py-2 bg-surface border border-[0.5px] border-border rounded-none focus:outline-none focus:border-border-focus text-text"
              >
                {addTagOptions.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={onAssignTag}
              disabled={!addTagId || tagAssignLoading}
              className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-none transition-colors disabled:opacity-50"
            >
              {tagAssignLoading ? (
                <LoadingSpinner size="sm" color="white" />
              ) : (
                <Plus size={18} />
              )}
              <span>Add</span>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function PeopleTab({
  people,
  loading,
  error,
  onRetry,
  onRowClick,
  onAddPerson,
}: {
  people: Person[]
  loading: boolean
  error: string | null
  onRetry: () => void
  onRowClick: (p: Person) => void
  onAddPerson: () => void
}) {
  const getFullName = (p: Person) => {
    return [p.first_name, p.middle_name, p.last_name].filter(Boolean).join(' ')
  }

  const columns: Column<Person>[] = [
    {
      id: 'name',
      header: 'Name',
      accessor: 'first_name',
      render: (_, row) => {
        const name = getFullName(row)
        return (
          <button
            onClick={() => onRowClick(row)}
            className="text-left text-primary hover:text-primary-hover font-medium"
          >
            {name || '—'}
          </button>
        )
      },
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'person_type',
      render: (v) => (
        <span className="text-text">
          {(v as string) === 'ClientEmployee' ? 'Employee' : 'Dependent'}
        </span>
      ),
    },
    {
      id: 'employee_code',
      header: 'Employee Code',
      accessor: 'employment_info',
      render: (value, row) => {
        if (row.person_type !== 'ClientEmployee') return '—'
        const empInfo = value as Person['employment_info']
        return <span className="text-text">{empInfo?.employee_code || '—'}</span>
      },
    },
    {
      id: 'dependent_of',
      header: 'Dependent of',
      accessor: 'dependent_info',
      render: (v, row) => {
        if (row.person_type !== 'Dependent') return '—'
        const depInfo = v as Person['dependent_info']
        if (!depInfo?.primary_employee_id) return '—'
        const primary = people.find((p) => p.id === depInfo.primary_employee_id)
        if (!primary) return '—'
        const name = getFullName(primary)
        return (
          <button
            onClick={() => onRowClick(primary)}
            className="text-left text-primary hover:text-primary-hover font-medium"
          >
            {name}
          </button>
        )
      },
    },
    {
      id: 'relationship',
      header: 'Relationship',
      accessor: 'dependent_info',
      render: (v, row) => {
        if (row.person_type !== 'Dependent') return '—'
        const depInfo = v as Person['dependent_info']
        return <span className="text-text">{depInfo?.relationship || '—'}</span>
      },
    },
    {
      id: 'contact',
      header: 'Contact',
      accessor: 'contact_info',
      render: (v) => {
        const c = v as Person['contact_info']
        return (
          <span className="text-text">
            {c?.email || c?.phone || '—'}
          </span>
        )
      },
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      render: (v) => <StatusBadge status={v as BaseStatus} size="sm" />,
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text">Employees & dependants</h2>
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            onAddPerson()
          }}
          className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-none transition-colors"
        >
          <Plus size={18} />
          Add person
        </button>
      </div>
      {people.length === 0 && !loading && !error ? (
        <EmptyState
          title="No employees or dependants"
          message="Add employees and their dependants for this client."
          variant="no-data"
          action={{
            label: 'Add first person',
            onClick: () => {
              onAddPerson()
            },
          }}
        />
      ) : (
        <DataTable<Person>
          data={people}
          columns={columns}
          loading={loading}
          error={error}
          onRetry={onRetry}
          emptyMessage="No employees or dependants for this client."
        />
      )}
    </div>
  )
}

function ContactsTab({
  contacts,
  loading,
  error,
  onRetry,
  onRowClick,
  onAddContact,
}: {
  contacts: Contact[]
  loading: boolean
  error: string | null
  onRetry: () => void
  onRowClick: (c: Contact) => void
  onAddContact: () => void
}) {
  const columns: Column<Contact>[] = [
    {
      id: 'name',
      header: 'Name',
      accessor: 'first_name',
      render: (_, row) => {
        const name = [row.first_name, row.last_name].filter(Boolean).join(' ')
        return (
          <button
            onClick={() => onRowClick(row)}
            className="text-left text-primary hover:text-primary-hover font-medium"
          >
            {name || '—'}
          </button>
        )
      },
    },
    {
      id: 'title',
      header: 'Title',
      accessor: 'title',
      render: (v) => <span className="text-text">{(v as string) || '—'}</span>,
    },
    {
      id: 'contact',
      header: 'Contact',
      accessor: 'contact_info',
      render: (v) => {
        const c = v as Contact['contact_info']
        return (
          <span className="text-text">
            {c?.email || c?.phone || '—'}
          </span>
        )
      },
    },
    {
      id: 'primary',
      header: 'Primary',
      accessor: 'is_primary',
      render: (v) =>
        (v as boolean) ? (
          <span className="inline-flex items-center gap-1 text-nurturing">
            <Star size={14} />
            Primary
          </span>
        ) : (
          '—'
        ),
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      render: (v) => <StatusBadge status={v as BaseStatus} size="sm" />,
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text">Contacts</h2>
        <button
          onClick={onAddContact}
          className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-none transition-colors"
        >
          <Plus size={18} />
          Add contact
        </button>
      </div>
      {contacts.length === 0 && !loading && !error ? (
        <EmptyState
          title="No contacts"
          message="Add contacts for this client."
          variant="no-data"
          action={{ label: 'Add first contact', onClick: onAddContact }}
        />
      ) : (
        <DataTable<Contact>
          data={contacts}
          columns={columns}
          loading={loading}
          error={error}
          onRetry={onRetry}
          emptyMessage="No contacts for this client."
        />
      )}
    </div>
  )
}

function ContractsTab({
  contracts,
  loading,
  error,
  onRetry,
  onRowClick,
  onAddContract,
}: {
  contracts: Contract[]
  loading: boolean
  error: string | null
  onRetry: () => void
  onRowClick: (c: Contract) => void
  onAddContract: () => void
}) {
  const now = new Date()
  const thirtyDays = 30 * 24 * 60 * 60 * 1000
  const isRenewalSoon = (c: Contract) => {
    const d = c.renewal_date || c.end_date
    if (!d) return false
    const t = new Date(d).getTime()
    return t >= now.getTime() && t - now.getTime() <= thirtyDays
  }
  const totalValue = contracts.reduce((acc, c) => acc + (c.billing_amount ?? 0), 0)

  const columns: Column<Contract>[] = [
    {
      id: 'number',
      header: 'Contract',
      accessor: 'contract_number',
      render: (v, row) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => onRowClick(row)}
            className="text-left text-primary hover:text-primary-hover font-medium"
          >
            {(v as string) || `#${row.id.slice(0, 8)}`}
          </button>
          {isRenewalSoon(row) && (
            <span className="text-xs px-2 py-0.5 bg-nurturing/20 text-nurturing-dark border border-nurturing">
              Renewal soon
            </span>
          )}
        </div>
      ),
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      render: (v) => <StatusBadge status={v as ContractStatus} size="sm" />,
    },
    {
      id: 'start_date',
      header: 'Start',
      accessor: 'start_date',
      render: (v) =>
        v ? new Date(v as string).toLocaleDateString() : '—',
    },
    {
      id: 'end_date',
      header: 'End',
      accessor: 'end_date',
      render: (v) =>
        v ? new Date(v as string).toLocaleDateString() : '—',
    },
    {
      id: 'billing',
      header: 'Billing',
      accessor: 'billing_amount',
      render: (_v, row) => {
        const amt = row.billing_amount
        if (amt == null) return '—'
        const cur = row.currency ?? 'USD'
        return (
          <span className="text-text">
            {new Intl.NumberFormat(undefined, {
              style: 'currency',
              currency: cur,
            }).format(amt)}
            {row.billing_frequency && (
              <span className="text-text-muted text-xs"> / {row.billing_frequency}</span>
            )}
          </span>
        )
      },
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-text">Contracts</h2>
          {contracts.length > 0 && totalValue > 0 && (
            <p className="text-sm text-text-muted">
              Total value:{' '}
              <span className="font-medium text-text">
                {new Intl.NumberFormat(undefined, {
                  style: 'currency',
                  currency: (contracts.find((c) => c.currency)?.currency ?? 'USD') as string,
                }).format(totalValue)}
              </span>
            </p>
          )}
        </div>
        <button
          onClick={onAddContract}
          className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-none transition-colors"
        >
          <Plus size={18} />
          Add contract
        </button>
      </div>
      {contracts.length === 0 && !loading && !error ? (
        <EmptyState
          title="No contracts"
          message="Add contracts for this client."
          variant="no-data"
          action={{ label: 'Add first contract', onClick: onAddContract }}
        />
      ) : (
        <DataTable<Contract>
          data={contracts}
          columns={columns}
          loading={loading}
          error={error}
          onRetry={onRetry}
          emptyMessage="No contracts for this client."
        />
      )}
    </div>
  )
}

function SessionsTab({
  sessions,
  loading,
  error,
  onRetry,
  onRowClick,
}: {
  sessions: ServiceSession[]
  loading: boolean
  error: string | null
  onRetry: () => void
  onRowClick: (s: ServiceSession) => void
}) {
  const columns: Column<ServiceSession>[] = [
    {
      id: 'scheduled_at',
      header: 'Scheduled',
      accessor: 'scheduled_at',
      render: (v, row) => (
        <button
          onClick={() => onRowClick(row)}
          className="text-left text-primary hover:text-primary-hover font-medium"
        >
          {v ? new Date(v as string).toLocaleString() : '—'}
        </button>
      ),
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      render: (v) => <StatusBadge status={v as SessionStatus} size="sm" />,
    },
    {
      id: 'location',
      header: 'Location',
      accessor: 'location',
      render: (v) => (
        <span className="text-text">{(v as string) || '—'}</span>
      ),
    },
  ]

  return (
    <div>
      <h2 className="text-lg font-semibold text-text mb-4">Sessions</h2>
      <DataTable<ServiceSession>
        data={sessions}
        columns={columns}
        loading={loading}
        error={error}
        onRetry={onRetry}
        emptyMessage="No sessions for this client’s contracts."
      />
    </div>
  )
}
