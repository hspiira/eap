/**
 * Client Detail Page
 * Tabs: Overview (summary, stats, events), People, Contracts, Reports
 */

import { createFileRoute, useNavigate, Link } from '@tanstack/react-router'
import { useState, useEffect, useCallback } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Breadcrumb } from '@/components/common/Breadcrumb'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LifecycleActions } from '@/components/common/LifecycleActions'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { DataTable, type Column } from '@/components/common/DataTable'
import { EmptyState } from '@/components/common/EmptyState'
import { useToast } from '@/contexts/ToastContext'
import { clientsApi } from '@/api/endpoints/clients'
import { clientTagsApi } from '@/api/endpoints/client-tags'
import { contactsApi } from '@/api/endpoints/contacts'
import { personsApi } from '@/api/endpoints/persons'
import { contractsApi } from '@/api/endpoints/contracts'
import { activitiesApi } from '@/api/endpoints/activities'
import { industriesApi } from '@/api/endpoints/industries'
import { serviceSessionsApi } from '@/api/endpoints/service-sessions'
import { CreateModal } from '@/components/common/CreateModal'
import { CreateActivityForm } from '@/components/forms/CreateActivityForm'
import { CreateContactForm } from '@/components/forms/CreateContactForm'
import { CreateContractForm } from '@/components/forms/CreateContractForm'
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
  const [lifecycleReasonModal, setLifecycleReasonModal] = useState<{ action: 'suspend' | 'terminate'; reason: string } | null>(null)

  const [activityModalOpen, setActivityModalOpen] = useState(false)
  const [contactModalOpen, setContactModalOpen] = useState(false)
  const [contractModalOpen, setContractModalOpen] = useState(false)
  const [editClientModalOpen, setEditClientModalOpen] = useState(false)
  const [activityModalLoading, setActivityModalLoading] = useState(false)
  const [contactModalLoading, setContactModalLoading] = useState(false)
  const [contractModalLoading, setContractModalLoading] = useState(false)
  const [editClientModalLoading, setEditClientModalLoading] = useState(false)

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
          await clientsApi.verify(clientId)
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
          setLifecycleReasonModal({ action: action as 'suspend' | 'terminate', reason: '' })
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

  const handleLifecycleReasonConfirm = async () => {
    if (!clientId || !lifecycleReasonModal || !lifecycleReasonModal.reason.trim()) return
    const { action, reason } = lifecycleReasonModal
    try {
      setActionLoading(true)
      if (action === 'suspend') {
        await clientsApi.suspend(clientId, reason.trim())
        showSuccess('Client suspended')
      } else {
        await clientsApi.terminate(clientId, reason.trim())
        showSuccess('Client terminated')
      }
      setLifecycleReasonModal(null)
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
    setActivityModalOpen(false)
    fetchActivities()
  }

  const handleContactCreated = () => {
    setContactModalOpen(false)
    fetchContacts()
  }

  const handleContractCreated = () => {
    setContractModalOpen(false)
    fetchContracts()
  }

  const handleClientUpdated = () => {
    setEditClientModalOpen(false)
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

        <div className="flex items-center gap-4 flex-wrap mb-4">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-safe">{client.name}</h1>
            <button
              onClick={() => setEditClientModalOpen(true)}
              className="p-1.5 text-safe hover:text-natural hover:bg-gray-100 rounded-none transition-colors"
              aria-label="Edit client"
            >
              <Edit size={18} />
            </button>
          </div>
          {client.is_verified && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-natural/10 border border-[0.5px] border-natural/30 text-natural text-sm">
              <CheckCircle size={16} />
              Verified
            </span>
          )}
          <StatusBadge status={client.status as BaseStatus} />
          {!client.is_verified && (
            <button
              type="button"
              onClick={() => handleAction('verify')}
              disabled={actionLoading}
              className="flex items-center gap-2 px-4 py-2 border border-[0.5px] border-natural rounded-none bg-safe hover:bg-safe-dark text-white transition-colors disabled:opacity-50"
            >
              <CheckCircle size={16} />
              Verify
            </button>
          )}
          <LifecycleActions
            currentStatus={client.status}
            onAction={handleAction}
            loading={actionLoading}
          />
        </div>

        {/* Tabs */}
        <div className="border-b border-safe/30 mb-4">
          <nav className="flex gap-1" aria-label="Client sections">
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
                  className={`flex items-center gap-2 px-3 py-2.5 text-sm font-medium border-b-2 transition-colors rounded-none ${
                    tab === id
                      ? 'border-natural text-natural'
                      : 'border-transparent text-safe hover:text-natural hover:border-safe'
                  }`}
                >
                  <Icon size={18} />
                  {label}
                  {count !== null && (
                    <span className="text-safe-light font-normal">({count})</span>
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
            onLogActivity={() => setActivityModalOpen(true)}
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
            onAddPerson={() =>
              navigate({
                to: '/people/client-people/new',
                search: { client_id: clientId },
              })
            }
          />
        )}

        {tab === 'contacts' && (
          <ContactsTab
            contacts={contacts}
            loading={contactsLoading}
            error={contactsError}
            onRetry={fetchContacts}
            onRowClick={(c) => navigate({ to: '/settings/contacts/$contactId', params: { contactId: c.id } })}
            onAddContact={() => setContactModalOpen(true)}
          />
        )}

        {tab === 'contracts' && (
          <ContractsTab
            contracts={contracts}
            loading={contractsLoading}
            error={contractsError}
            onRetry={fetchContracts}
            onRowClick={(c) => navigate({ to: `/contracts/${c.id}` })}
            onAddContract={() => setContractModalOpen(true)}
          />
        )}

        {tab === 'sessions' && (
          <SessionsTab
            sessions={sessions}
            loading={sessionsLoading}
            error={sessionsError}
            onRetry={fetchSessions}
            onRowClick={(s) => navigate({ to: `/sessions/${s.id}` })}
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
          isOpen={activityModalOpen}
          onClose={() => setActivityModalOpen(false)}
          title="Log activity"
          loading={activityModalLoading}
        >
          <CreateActivityForm
            initialClientId={clientId}
            onSuccess={handleActivityCreated}
            onCancel={() => setActivityModalOpen(false)}
            onLoadingChange={setActivityModalLoading}
          />
        </CreateModal>

        <CreateModal
          isOpen={contactModalOpen}
          onClose={() => setContactModalOpen(false)}
          title="Add contact"
          loading={contactModalLoading}
        >
          <CreateContactForm
            initialClientId={clientId}
            onSuccess={handleContactCreated}
            onCancel={() => setContactModalOpen(false)}
            onLoadingChange={setContactModalLoading}
          />
        </CreateModal>

        <CreateModal
          isOpen={contractModalOpen}
          onClose={() => setContractModalOpen(false)}
          title="Add contract"
          loading={contractModalLoading}
        >
          <CreateContractForm
            initialClientId={clientId}
            onSuccess={handleContractCreated}
            onCancel={() => setContractModalOpen(false)}
            onLoadingChange={setContractModalLoading}
          />
        </CreateModal>

        <CreateModal
          isOpen={editClientModalOpen}
          onClose={() => setEditClientModalOpen(false)}
          title="Edit client"
          loading={editClientModalLoading}
        >
          <EditClientForm
            client={client}
            onSuccess={handleClientUpdated}
            onCancel={() => setEditClientModalOpen(false)}
            onLoadingChange={setEditClientModalLoading}
          />
        </CreateModal>

        {lifecycleReasonModal && (
          <div className="fixed inset-0 bg-safe/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white border border-[0.5px] border-safe/30 max-w-md w-full p-6">
              <h3 className="text-lg font-semibold text-safe mb-2">
                {lifecycleReasonModal.action === 'suspend' ? 'Suspend client' : 'Terminate client'}
              </h3>
              <p className="text-safe text-sm mb-4">
                {lifecycleReasonModal.action === 'suspend'
                  ? 'A reason is required to suspend this client.'
                  : 'A reason is required to terminate this client. This action is permanent.'}
              </p>
              <textarea
                value={lifecycleReasonModal.reason}
                onChange={(e) =>
                  setLifecycleReasonModal({ ...lifecycleReasonModal, reason: e.target.value })
                }
                placeholder="Enter reason..."
                className="w-full px-4 py-2 bg-white border border-[0.5px] border-safe/30 rounded-none focus:outline-none focus:border-natural text-safe mb-4 min-h-[80px]"
                rows={3}
              />
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => setLifecycleReasonModal(null)}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-white hover:bg-gray-100 text-safe border border-[0.5px] border-safe/30 rounded-none transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleLifecycleReasonConfirm}
                  disabled={actionLoading || !lifecycleReasonModal.reason.trim()}
                  className="px-4 py-2 bg-natural-dark hover:bg-natural text-white rounded-none transition-colors disabled:opacity-50"
                >
                  {actionLoading ? 'Processing...' : 'Confirm'}
                </button>
              </div>
            </div>
          </div>
        )}
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
          className="bg-white border border-[0.5px] border-safe/30 p-4 hover:border-natural transition-colors block"
        >
          <div className="flex items-center gap-2 text-safe mb-1">
            <Users size={20} />
            <span className="text-sm font-medium">People</span>
          </div>
          <p className="text-2xl font-bold text-safe">{peopleCount}</p>
          <p className="text-xs text-safe-light">Employees & dependants</p>
        </Link>
        <Link
          to="."
          search={{ tab: 'contacts' }}
          className="bg-white border border-[0.5px] border-safe/30 p-4 hover:border-natural transition-colors block"
        >
          <div className="flex items-center gap-2 text-safe mb-1">
            <UserCircle size={20} />
            <span className="text-sm font-medium">Contacts</span>
          </div>
          <p className="text-2xl font-bold text-safe">{contactsCount}</p>
        </Link>
        <Link
          to="."
          search={{ tab: 'contracts' }}
          className="bg-white border border-[0.5px] border-safe/30 p-4 hover:border-natural transition-colors block"
        >
          <div className="flex items-center gap-2 text-safe mb-1">
            <FileText size={20} />
            <span className="text-sm font-medium">Contracts</span>
          </div>
          <p className="text-2xl font-bold text-safe">{clientStats?.contract_count ?? contractsCount}</p>
        </Link>
        {(clientStats?.child_count ?? 0) > 0 && (
          <div className="bg-white border border-[0.5px] border-safe/30 p-4">
            <div className="flex items-center gap-2 text-safe mb-1">
              <Building2 size={20} />
              <span className="text-sm font-medium">Child clients</span>
            </div>
            <p className="text-2xl font-bold text-safe">{clientStats?.child_count ?? 0}</p>
            <p className="text-xs text-safe-light">Sub-clients</p>
          </div>
        )}
      </div>

      {/* Child clients list (when parent) */}
      {(childClients.length > 0 || childClientsLoading) && (
        <div className="bg-white border border-[0.5px] border-safe/30 p-6">
          <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
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
                <li key={c.id} className="flex items-center justify-between py-2 border-b border-safe/20 last:border-0">
                  <div>
                    <p className="text-safe font-medium">{c.name}</p>
                    {c.code && <p className="text-sm text-safe-light">Code: {c.code}</p>}
                  </div>
                  <button
                    type="button"
                    onClick={() => onViewClient(c.id)}
                    className="text-natural hover:text-natural-dark text-sm font-medium"
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
          <div className="bg-white border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Building2 size={20} />
              Summary
            </h2>
            <dl className="space-y-2 text-sm">
              <div className="flex gap-2">
                <dt className="text-safe-light w-28">Status</dt>
                <dd>
                  <StatusBadge status={client.status as BaseStatus} size="sm" />
                </dd>
              </div>
              {client.code && (
                <div className="flex gap-2">
                  <dt className="text-safe-light w-28">Code</dt>
                  <dd className="text-safe">{client.code}</dd>
                </div>
              )}
              {(industryName || client.industry_id) && (
                <div className="flex gap-2">
                  <dt className="text-safe-light w-28">Industry</dt>
                  <dd className="text-safe">{industryName ?? client.industry_id}</dd>
                </div>
              )}
              {client.contact_info?.email && (
                <div className="flex gap-2">
                  <dt className="text-safe-light w-28 flex items-center gap-1">
                    <Mail size={14} /> Email
                  </dt>
                  <dd className="text-safe">{client.contact_info.email}</dd>
                </div>
              )}
              {client.contact_info?.phone && (
                <div className="flex gap-2">
                  <dt className="text-safe-light w-28 flex items-center gap-1">
                    <Phone size={14} /> Phone
                  </dt>
                  <dd className="text-safe">{client.contact_info.phone}</dd>
                </div>
              )}
              {client.contact_info?.address && (
                <div className="flex gap-2">
                  <dt className="text-safe-light w-28 flex items-center gap-1">
                    <MapPin size={14} /> Contact address
                  </dt>
                  <dd className="text-safe">{client.contact_info.address}</dd>
                </div>
              )}
              {client.billing_address && (client.billing_address.city || client.billing_address.country || client.billing_address.street) && (
                <div className="flex gap-2">
                  <dt className="text-safe-light w-28 flex items-center gap-1">
                    <MapPin size={14} /> Billing address
                  </dt>
                  <dd className="text-safe">
                    {[client.billing_address.street, client.billing_address.city, client.billing_address.postal_code, client.billing_address.country]
                      .filter(Boolean)
                      .join(', ')}
                  </dd>
                </div>
              )}
              {client.preferred_contact_method && (
                <div className="flex gap-2">
                  <dt className="text-safe-light w-28">Preferred contact</dt>
                  <dd className="text-safe capitalize">{client.preferred_contact_method}</dd>
                </div>
              )}
              <div className="flex gap-2">
                <dt className="text-safe-light w-28">Updated</dt>
                <dd className="text-safe">
                  {new Date(client.updated_at).toLocaleString()}
                </dd>
              </div>
            </dl>
          </div>

          {primaryContact && (
            <div className="bg-white border border-[0.5px] border-safe/30 p-6">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <Star size={20} className="text-nurturing" />
                Primary contact
              </h2>
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="font-medium text-safe">
                    {[primaryContact.first_name, primaryContact.last_name].filter(Boolean).join(' ')}
                  </p>
                  {primaryContact.title && (
                    <p className="text-sm text-safe-light">{primaryContact.title}</p>
                  )}
                  {primaryContact.contact_info?.email && (
                    <p className="text-sm text-safe-light">{primaryContact.contact_info.email}</p>
                  )}
                  {primaryContact.contact_info?.phone && !primaryContact.contact_info?.email && (
                    <p className="text-sm text-safe-light">{primaryContact.contact_info.phone}</p>
                  )}
                </div>
                <Link
                  to="/settings/contacts/$contactId"
                  params={{ contactId: primaryContact.id }}
                  className="text-natural hover:text-natural-dark text-sm font-medium flex-shrink-0"
                >
                  View
                </Link>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="bg-white border border-[0.5px] border-safe/30 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-safe flex items-center gap-2">
                <ActivityIcon size={20} />
                Recent events
              </h2>
              <button
                onClick={onLogActivity}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
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
                <p className="text-safe-light text-sm">No recent activity.</p>
                <button
                  onClick={onLogActivity}
                  className="mt-2 text-natural hover:text-natural-dark text-sm font-medium"
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
                      className="flex items-start gap-2 py-2 border-b border-safe/20 last:border-0"
                    >
                      <span className="text-safe-light text-xs uppercase font-medium mt-0.5">
                        {a.activity_type}
                      </span>
                      <div className="flex-1 min-w-0">
                        {a.title && (
                          <p className="text-safe font-medium truncate">{a.title}</p>
                        )}
                        {a.description && (
                          <p className="text-safe-light text-sm truncate">{a.description}</p>
                        )}
                        <p className="text-safe-light text-xs mt-1">
                          {new Date(a.occurred_at).toLocaleString()}
                        </p>
                      </div>
                      <button
                        onClick={() => onViewActivity(a.id)}
                        className="text-natural hover:text-natural-dark text-sm font-medium flex-shrink-0"
                      >
                        View
                      </button>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={onViewAllActivities}
                  className="mt-3 text-natural hover:text-natural-dark text-sm font-medium"
                >
                  View all activities
                </button>
              </>
            )}
          </div>

          {hasContracts && (
            <div className="bg-white border border-[0.5px] border-safe/30 p-6">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
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
                  <p className="text-safe-light text-sm">No upcoming sessions.</p>
                ) : (
                <ul className="space-y-2">
                  {upcoming.map((s) => (
                    <li
                      key={s.id}
                      className="flex items-center justify-between py-2 border-b border-safe/20 last:border-0"
                    >
                      <div>
                        <p className="text-safe font-medium">
                          {new Date(s.scheduled_at).toLocaleString()}
                        </p>
                        {s.location && (
                          <p className="text-sm text-safe-light">{s.location}</p>
                        )}
                      </div>
                      <Link
                        to={`/sessions/${s.id}`}
                        className="text-natural hover:text-natural-dark text-sm font-medium"
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
      <div className="bg-white border border-[0.5px] border-safe/30 p-6">
        <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
          <Tag size={20} />
          Tags
        </h2>
        {tags.length > 0 && (
          <ul className="space-y-2 mb-4">
            {tags.map((t) => (
              <li
                key={t.id}
                className="flex items-center justify-between py-2 px-3 rounded-none hover:bg-safe-light/5 group"
              >
                <button
                  onClick={() => onTagClick(t.id)}
                  className="flex items-center gap-2 text-left text-natural hover:text-natural-dark font-medium"
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
          <p className="text-safe-light text-sm mb-4">No tags assigned.</p>
        )}
        {assignableTags.length > 0 && (
          <div className="flex flex-wrap gap-2 items-end">
            <div className="flex-1 min-w-[200px]">
              <label htmlFor="addTag" className="block text-sm font-medium text-safe-light mb-1">
                Add tag
              </label>
              <select
                id="addTag"
                value={addTagId}
                onChange={(e) => setAddTagId(e.target.value)}
                className="w-full px-4 py-2 bg-white border border-[0.5px] border-safe/30 rounded-none focus:outline-none focus:border-natural text-safe"
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
              className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors disabled:opacity-50"
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

  const getPrimaryEmployeeName = (depInfo: Person['dependent_info']) => {
    if (!depInfo?.primary_employee_id) return '—'
    const primary = people.find((p) => p.id === depInfo.primary_employee_id)
    if (!primary) return '—'
    return getFullName(primary)
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
            className="text-left text-natural hover:text-natural-dark font-medium"
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
        <span className="text-safe">
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
        return <span className="text-safe">{empInfo?.employee_code || '—'}</span>
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
            className="text-left text-natural hover:text-natural-dark font-medium"
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
        return <span className="text-safe">{depInfo?.relationship || '—'}</span>
      },
    },
    {
      id: 'contact',
      header: 'Contact',
      accessor: 'contact_info',
      render: (v) => {
        const c = v as Person['contact_info']
        return (
          <span className="text-safe">
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
        <h2 className="text-lg font-semibold text-safe">Employees & dependants</h2>
        <button
          onClick={onAddPerson}
          className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
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
          action={{ label: 'Add first person', onClick: onAddPerson }}
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
            className="text-left text-natural hover:text-natural-dark font-medium"
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
      render: (v) => <span className="text-safe">{(v as string) || '—'}</span>,
    },
    {
      id: 'contact',
      header: 'Contact',
      accessor: 'contact_info',
      render: (v) => {
        const c = v as Contact['contact_info']
        return (
          <span className="text-safe">
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
        <h2 className="text-lg font-semibold text-safe">Contacts</h2>
        <button
          onClick={onAddContact}
          className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
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
            className="text-left text-natural hover:text-natural-dark font-medium"
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
      render: (v, row) => {
        const amt = row.billing_amount
        if (amt == null) return '—'
        const cur = row.currency ?? 'USD'
        return (
          <span className="text-safe">
            {new Intl.NumberFormat(undefined, {
              style: 'currency',
              currency: cur,
            }).format(amt)}
            {row.billing_frequency && (
              <span className="text-safe-light text-xs"> / {row.billing_frequency}</span>
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
          <h2 className="text-lg font-semibold text-safe">Contracts</h2>
          {contracts.length > 0 && totalValue > 0 && (
            <p className="text-sm text-safe-light">
              Total value:{' '}
              <span className="font-medium text-safe">
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
          className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
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
          className="text-left text-natural hover:text-natural-dark font-medium"
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
        <span className="text-safe">{(v as string) || '—'}</span>
      ),
    },
  ]

  return (
    <div>
      <h2 className="text-lg font-semibold text-safe mb-4">Sessions</h2>
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
