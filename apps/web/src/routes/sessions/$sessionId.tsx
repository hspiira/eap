/**
 * Service Session Detail Page
 * Displays session information, reschedule, complete, cancel, no-show, and feedback functionality
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { FormField } from '@/components/common/FormField'
import { DatePicker } from '@/components/common/DatePicker'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { useToast } from '@/contexts/ToastContext'
import { serviceSessionsApi } from '@/api/endpoints/service-sessions'
import { personsApi } from '@/api/endpoints/persons'
import { servicesApi } from '@/api/endpoints/services'
import type { ServiceSession } from '@/types/entities'
import type { SessionStatus } from '@/types/enums'
import { Calendar, MapPin, FileText, CheckCircle, XCircle, UserX, MessageSquare, Edit } from 'lucide-react'

export const Route = createFileRoute('/sessions/$sessionId')({
  component: SessionDetailPage,
})

function SessionDetailPage() {
  const { sessionId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [session, setSession] = useState<ServiceSession | null>(null)
  const [person, setPerson] = useState<{ id: string; name: string } | null>(null)
  const [service, setService] = useState<{ id: string; name: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showRescheduleDialog, setShowRescheduleDialog] = useState(false)
  const [showFeedbackDialog, setShowFeedbackDialog] = useState(false)
  const [rescheduleDate, setRescheduleDate] = useState('')
  const [rescheduleTime, setRescheduleTime] = useState('')
  const [rescheduleNotes, setRescheduleNotes] = useState('')
  const [feedbackRating, setFeedbackRating] = useState('')
  const [feedbackComments, setFeedbackComments] = useState('')

  const fetchSession = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await serviceSessionsApi.getById(sessionId)
      setSession(data)

      // Fetch person and service info
      try {
        const [personData, serviceData] = await Promise.all([
          personsApi.getById(data.person_id),
          servicesApi.getById(data.service_id),
        ])
        setPerson({ 
          id: personData.id, 
          name: `${personData.first_name} ${personData.last_name}`.trim() 
        })
        setService({ id: serviceData.id, name: serviceData.name })
      } catch (err) {
        console.error('Error fetching related data:', err)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load session')
      showError('Failed to load session')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSession()
  }, [sessionId])

  const handleComplete = async () => {
    try {
      setActionLoading(true)
      const updatedSession = await serviceSessionsApi.complete(sessionId)
      setSession(updatedSession)
      showSuccess('Session marked as completed')
    } catch (err: any) {
      showError(`Failed to complete session: ${err.message || 'Unknown error'}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleCancel = async () => {
    try {
      setActionLoading(true)
      const updatedSession = await serviceSessionsApi.cancel(sessionId)
      setSession(updatedSession)
      showSuccess('Session cancelled')
    } catch (err: any) {
      showError(`Failed to cancel session: ${err.message || 'Unknown error'}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleNoShow = async () => {
    try {
      setActionLoading(true)
      const updatedSession = await serviceSessionsApi.noShow(sessionId)
      setSession(updatedSession)
      showSuccess('Session marked as no-show')
    } catch (err: any) {
      showError(`Failed to mark no-show: ${err.message || 'Unknown error'}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleReschedule = async () => {
    if (!rescheduleDate || !rescheduleTime) {
      showError('Please select both date and time')
      return
    }

    try {
      setActionLoading(true)
      const scheduledAt = new Date(`${rescheduleDate}T${rescheduleTime}`).toISOString()
      const updatedSession = await serviceSessionsApi.reschedule(sessionId, {
        scheduled_at: scheduledAt,
        notes: rescheduleNotes || null,
      })
      setSession(updatedSession)
      setShowRescheduleDialog(false)
      setRescheduleDate('')
      setRescheduleTime('')
      setRescheduleNotes('')
      showSuccess('Session rescheduled successfully')
    } catch (err: any) {
      showError(`Failed to reschedule session: ${err.message || 'Unknown error'}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleSubmitFeedback = async () => {
    try {
      setActionLoading(true)
      const updatedSession = await serviceSessionsApi.updateFeedback(sessionId, {
        rating: feedbackRating ? parseInt(feedbackRating) : null,
        comments: feedbackComments || null,
      })
      setSession(updatedSession)
      setShowFeedbackDialog(false)
      setFeedbackRating('')
      setFeedbackComments('')
      showSuccess('Feedback submitted successfully')
    } catch (err: any) {
      showError(`Failed to submit feedback: ${err.message || 'Unknown error'}`)
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

  if (error || !session) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error || 'Session not found'}
            onRetry={fetchSession}
          />
        </div>
      </AppLayout>
    )
  }

  const formatDateTime = (dateString: string | null | undefined) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString()
  }

  const canReschedule = session.status === 'Scheduled' || session.status === 'Rescheduled'
  const canComplete = session.status === 'Scheduled' || session.status === 'Rescheduled'
  const canCancel = session.status === 'Scheduled' || session.status === 'Rescheduled'
  const canMarkNoShow = session.status === 'Scheduled' || session.status === 'Rescheduled'
  const canSubmitFeedback = session.status === 'Completed'

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-safe mb-2">Service Session</h1>
            <div className="flex items-center gap-4">
              <StatusBadge status={session.status as SessionStatus} />
              {person && (
                <span className="text-safe-light text-sm flex items-center gap-1">
                  <Calendar size={16} />
                  {formatDateTime(session.scheduled_at)}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            {canReschedule && (
              <button
                onClick={() => setShowRescheduleDialog(true)}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50"
              >
                <Edit size={18} />
                <span>Reschedule</span>
              </button>
            )}
            {canComplete && (
              <button
                onClick={handleComplete}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors disabled:opacity-50"
              >
                <CheckCircle size={18} />
                <span>Complete</span>
              </button>
            )}
            {canCancel && (
              <button
                onClick={handleCancel}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-nurturing hover:bg-nurturing-dark text-white rounded-none transition-colors disabled:opacity-50"
              >
                <XCircle size={18} />
                <span>Cancel</span>
              </button>
            )}
            {canMarkNoShow && (
              <button
                onClick={handleNoShow}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50"
              >
                <UserX size={18} />
                <span>No Show</span>
              </button>
            )}
            {canSubmitFeedback && !session.feedback && (
              <button
                onClick={() => setShowFeedbackDialog(true)}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors disabled:opacity-50"
              >
                <MessageSquare size={18} />
                <span>Add Feedback</span>
              </button>
            )}
          </div>
        </div>

        {/* Session Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Session Details */}
          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Calendar size={20} />
              Session Details
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Status</dt>
                <dd className="text-safe mt-1">
                  <StatusBadge status={session.status as SessionStatus} size="sm" />
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Scheduled At</dt>
                <dd className="text-safe mt-1 flex items-center gap-2">
                  <Calendar size={16} />
                  {formatDateTime(session.scheduled_at)}
                </dd>
              </div>
              {session.completed_at && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Completed At</dt>
                  <dd className="text-safe mt-1">{formatDateTime(session.completed_at)}</dd>
                </div>
              )}
              {session.location && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Location</dt>
                  <dd className="text-safe mt-1 flex items-center gap-2">
                    <MapPin size={16} />
                    {session.location}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Participants */}
          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <FileText size={20} />
              Participants
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Person</dt>
                <dd className="text-safe mt-1">{person?.name || session.person_id}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Service</dt>
                <dd className="text-safe mt-1">{service?.name || session.service_id}</dd>
              </div>
              {session.service_provider_id && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Service Provider</dt>
                  <dd className="text-safe mt-1">{session.service_provider_id}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Notes */}
          {session.notes && (
            <div className="bg-calm border border-[0.5px] border-safe p-6 md:col-span-2">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <FileText size={20} />
                Notes
              </h2>
              <p className="text-safe">{session.notes}</p>
            </div>
          )}

          {/* Feedback */}
          {session.feedback && (
            <div className="bg-calm border border-[0.5px] border-safe p-6 md:col-span-2">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <MessageSquare size={20} />
                Feedback
              </h2>
              <dl className="space-y-3">
                {session.feedback.rating !== null && session.feedback.rating !== undefined && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Rating</dt>
                    <dd className="text-safe mt-1">
                      {session.feedback.rating}/5 ⭐
                    </dd>
                  </div>
                )}
                {session.feedback.comments && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Comments</dt>
                    <dd className="text-safe mt-1">{session.feedback.comments}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}
        </div>

        {/* Reschedule Dialog */}
        {showRescheduleDialog && (
          <ConfirmDialog
            title="Reschedule Session"
            message="Select a new date and time for this session"
            onConfirm={handleReschedule}
            onCancel={() => {
              setShowRescheduleDialog(false)
              setRescheduleDate('')
              setRescheduleTime('')
              setRescheduleNotes('')
            }}
            confirmText="Reschedule"
            cancelText="Cancel"
            loading={actionLoading}
          >
            <div className="space-y-4 mt-4">
              <DatePicker
                label="New Date"
                name="reschedule_date"
                value={rescheduleDate}
                onChange={setRescheduleDate}
                required
              />
              <FormField
                label="New Time"
                name="reschedule_time"
                type="time"
                value={rescheduleTime}
                onChange={(e) => setRescheduleTime(e.target.value)}
                required
              />
              <FormField
                label="Notes (optional)"
                name="reschedule_notes"
                type="textarea"
                value={rescheduleNotes}
                onChange={(e) => setRescheduleNotes(e.target.value)}
                rows={3}
              />
            </div>
          </ConfirmDialog>
        )}

        {/* Feedback Dialog */}
        {showFeedbackDialog && (
          <ConfirmDialog
            title="Session Feedback"
            message="Please provide feedback for this session"
            onConfirm={handleSubmitFeedback}
            onCancel={() => {
              setShowFeedbackDialog(false)
              setFeedbackRating('')
              setFeedbackComments('')
            }}
            confirmText="Submit Feedback"
            cancelText="Cancel"
            loading={actionLoading}
          >
            <div className="space-y-4 mt-4">
              <FormField
                label="Rating (1-5)"
                name="feedback_rating"
                type="number"
                min="1"
                max="5"
                value={feedbackRating}
                onChange={(e) => setFeedbackRating(e.target.value)}
                placeholder="Enter rating from 1 to 5"
              />
              <FormField
                label="Comments"
                name="feedback_comments"
                type="textarea"
                value={feedbackComments}
                onChange={(e) => setFeedbackComments(e.target.value)}
                rows={4}
                placeholder="Enter your feedback comments"
              />
            </div>
          </ConfirmDialog>
        )}
      </div>
    </AppLayout>
  )
}
