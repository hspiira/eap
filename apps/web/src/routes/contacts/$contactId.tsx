/**
 * Contact Detail Page
 * Displays contact information, lifecycle actions, and set-as-primary
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LifecycleActions } from '@/components/common/LifecycleActions'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useToast } from '@/contexts/ToastContext'
import { contactsApi } from '@/api/endpoints/contacts'
import { clientsApi } from '@/api/endpoints/clients'
import type { Contact } from '@/types/entities'
import type { BaseStatus } from '@/types/enums'
import { Edit, UserCircle, Building2, Mail, Phone, Star } from 'lucide-react'

export const Route = createFileRoute('/contacts/$contactId')({
  component: ContactDetailPage,
})

function ContactDetailPage() {
  const { contactId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [contact, setContact] = useState<Contact | null>(null)
  const [client, setClient] = useState<{ id: string; name: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchContact = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await contactsApi.getById(contactId)
      setContact(data)
      try {
        const clientData = await clientsApi.getById(data.client_id)
        setClient({ id: clientData.id, name: clientData.name })
      } catch {
        /* ignore */
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load contact'
      setError(message)
      showError('Failed to load contact')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchContact()
  }, [contactId])

  const handleAction = async (action: string) => {
    try {
      setActionLoading(true)
      let updated: Contact
      switch (action) {
        case 'activate':
          updated = await contactsApi.activate(contactId)
          break
        case 'deactivate':
          updated = await contactsApi.deactivate(contactId)
          break
        default:
          throw new Error(`Unknown action: ${action}`)
      }
      setContact(updated)
      showSuccess(`Contact ${action}d successfully`)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      showError(`Failed to ${action} contact: ${message}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleSetPrimary = async () => {
    try {
      setActionLoading(true)
      const updated = await contactsApi.setPrimary(contactId)
      setContact(updated)
      showSuccess('Contact set as primary')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      showError(`Failed to set primary: ${message}`)
    } finally {
      setActionLoading(false)
    }
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

  if (error || !contact) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error ?? 'Contact not found'}
            onRetry={fetchContact}
          />
        </div>
      </AppLayout>
    )
  }

  const ci = contact.contact_info

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-safe mb-2 flex items-center gap-2">
              <UserCircle size={28} />
              {`${contact.first_name} ${contact.last_name}`.trim()}
              {contact.is_primary && (
                <Star size={20} className="text-natural" fill="currentColor" title="Primary contact" />
              )}
            </h1>
            <div className="flex items-center gap-4">
              <StatusBadge status={(contact.status as BaseStatus) ?? 'Active'} />
              {client && (
                <span className="text-safe-light text-sm flex items-center gap-1">
                  <Building2 size={16} />
                  {client.name}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <LifecycleActions
              currentStatus={contact.status}
              onAction={handleAction}
              loading={actionLoading}
              availableActions={['activate', 'deactivate']}
            />
            {!contact.is_primary && (
              <button
                onClick={handleSetPrimary}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors disabled:opacity-50"
              >
                <Star size={18} />
                <span>Set as Primary</span>
              </button>
            )}
            <button
              onClick={() => navigate({ to: `/contacts/${contactId}/edit` })}
              className="flex items-center gap-2 px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors"
            >
              <Edit size={18} />
              <span>Edit</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <UserCircle size={20} />
              Contact Details
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Name</dt>
                <dd className="text-safe mt-1">{`${contact.first_name} ${contact.last_name}`.trim()}</dd>
              </div>
              {contact.title && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Title</dt>
                  <dd className="text-safe mt-1">{contact.title}</dd>
                </div>
              )}
              <div>
                <dt className="text-sm font-medium text-safe-light">Status</dt>
                <dd className="text-safe mt-1">
                  <StatusBadge status={(contact.status as BaseStatus) ?? 'Active'} size="sm" />
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Primary</dt>
                <dd className="text-safe mt-1">{contact.is_primary ? 'Yes' : 'No'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Client</dt>
                <dd className="text-safe mt-1">
                  {client ? (
                    <button
                      onClick={() => navigate({ to: `/clients/${contact.client_id}` })}
                      className="text-natural hover:text-natural-dark font-medium"
                    >
                      {client.name}
                    </button>
                  ) : (
                    contact.client_id
                  )}
                </dd>
              </div>
            </dl>
          </div>

          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Mail size={20} />
              Contact Info
            </h2>
            {ci ? (
              <dl className="space-y-3">
                {ci.email && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Email</dt>
                    <dd className="text-safe mt-1 flex items-center gap-2">
                      <Mail size={16} />
                      {ci.email}
                    </dd>
                  </div>
                )}
                {ci.phone && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Phone</dt>
                    <dd className="text-safe mt-1 flex items-center gap-2">
                      <Phone size={16} />
                      {ci.phone}
                    </dd>
                  </div>
                )}
                {ci.mobile && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Mobile</dt>
                    <dd className="text-safe mt-1">{ci.mobile}</dd>
                  </div>
                )}
                {ci.preferred_method && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Preferred method</dt>
                    <dd className="text-safe mt-1">{ci.preferred_method}</dd>
                  </div>
                )}
              </dl>
            ) : (
              <p className="text-safe-light text-sm">No contact info</p>
            )}
          </div>

          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4">Metadata</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Created</dt>
                <dd className="text-safe mt-1">{new Date(contact.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Last updated</dt>
                <dd className="text-safe mt-1">{new Date(contact.updated_at).toLocaleString()}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
