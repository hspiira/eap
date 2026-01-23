/**
 * Documents List Page
 * Displays all documents within the current tenant with filtering, search, and pagination
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable, type Column } from '@/components/common/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { documentsApi } from '@/api/endpoints/documents'
import type { Document } from '@/types/entities'
import type { DocumentType, DocumentStatus } from '@/types/enums'
import { Plus, FileText } from 'lucide-react'

export const Route = createFileRoute('/documents/')({
  component: DocumentsPage,
})

function DocumentsPage() {
  const navigate = useNavigate()
  const { showError } = useToast()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [confidentialityFilter, setConfidentialityFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null)

  // Fetch documents (tenant-scoped automatically via API client)
  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const params: any = {
        page: currentPage,
        limit: pageSize,
      }

      if (searchValue) {
        params.search = searchValue
      }

      if (statusFilter) {
        params.status = statusFilter
      }

      if (typeFilter) {
        params.document_type = typeFilter
      }

      if (confidentialityFilter) {
        params.confidentiality_level = confidentialityFilter
      }

      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }

      const response = await documentsApi.list(params)
      setDocuments(response.items)
      setTotalItems(response.total)
    } catch (error) {
      showError('Failed to load documents')
      console.error('Error fetching documents:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [currentPage, pageSize, searchValue, statusFilter, typeFilter, confidentialityFilter, sortBy, sortDirection])

  const handleSort = (columnId: string) => {
    if (sortBy === columnId) {
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortBy(null)
        setSortDirection(null)
      } else {
        setSortDirection('asc')
      }
    } else {
      setSortBy(columnId)
      setSortDirection('asc')
    }
  }

  const handleRowClick = (document: Document) => {
    navigate({ to: `/documents/${document.id}` })
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'Draft', label: 'Draft' },
    { value: 'Published', label: 'Published' },
    { value: 'Archived', label: 'Archived' },
    { value: 'Expired', label: 'Expired' },
  ]

  const typeOptions = [
    { value: '', label: 'All Types' },
    { value: 'Contract', label: 'Contract' },
    { value: 'Certification', label: 'Certification' },
    { value: 'KPI Report', label: 'KPI Report' },
    { value: 'Feedback Summary', label: 'Feedback Summary' },
    { value: 'Billing Report', label: 'Billing Report' },
    { value: 'Utilization Report', label: 'Utilization Report' },
    { value: 'Other', label: 'Other' },
  ]

  const confidentialityOptions = [
    { value: '', label: 'All Levels' },
    { value: 'Public', label: 'Public' },
    { value: 'Internal', label: 'Internal' },
    { value: 'Confidential', label: 'Confidential' },
    { value: 'Restricted', label: 'Restricted' },
  ]

  const formatFileSize = (bytes: number | null | undefined) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const columns: Column<Document>[] = [
    {
      id: 'name',
      header: 'Document Name',
      accessor: 'name',
      sortable: true,
      render: (value, row) => (
        <button
          onClick={() => handleRowClick(row)}
          className="text-left text-natural hover:text-natural-dark font-medium flex items-center gap-2"
        >
          <FileText size={16} />
          {value as string}
        </button>
      ),
    },
    {
      id: 'document_type',
      header: 'Type',
      accessor: 'document_type',
      sortable: true,
      render: (value) => <span>{value as string}</span>,
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      sortable: true,
      render: (value) => <StatusBadge status={value as DocumentStatus} size="sm" />,
    },
    {
      id: 'version',
      header: 'Version',
      accessor: 'version',
      sortable: true,
      render: (value) => <span>{value ? `v${value}` : '-'}</span>,
    },
    {
      id: 'file_size',
      header: 'Size',
      accessor: 'file_size',
      sortable: true,
      render: (value) => <span className="text-safe-light text-sm">{formatFileSize(value as number)}</span>,
    },
    {
      id: 'confidentiality_level',
      header: 'Confidentiality',
      accessor: 'confidentiality_level',
      sortable: true,
      render: (value) => <span className="text-safe-light text-sm">{value || '-'}</span>,
    },
    {
      id: 'published_at',
      header: 'Published',
      accessor: 'published_at',
      sortable: true,
      render: (value) => {
        if (!value) return '-'
        return new Date(value as string).toLocaleDateString()
      },
    },
    {
      id: 'created_at',
      header: 'Created',
      accessor: 'created_at',
      sortable: true,
      render: (value) => {
        if (!value) return '-'
        const date = new Date(value as string)
        return date.toLocaleDateString()
      },
    },
  ]

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-safe">Documents</h1>
          <button
            onClick={() => navigate({ to: '/documents/new' })}
            className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
          >
            <Plus size={18} />
            <span>Upload Document</span>
          </button>
        </div>

        {loading && documents.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <DataTable
            data={documents}
            columns={columns}
            loading={loading}
            pagination={{
              currentPage,
              pageSize,
              totalItems,
              onPageChange: setCurrentPage,
              onPageSizeChange: (size) => {
                setPageSize(size)
                setCurrentPage(1)
              },
            }}
            sorting={{
              sortBy,
              sortDirection,
              onSort: handleSort,
            }}
            filters={{
              searchValue,
              onSearchChange: (value) => {
                setSearchValue(value)
                setCurrentPage(1)
              },
              searchPlaceholder: 'Search documents by name...',
              statusFilter: {
                value: statusFilter,
                options: statusOptions,
                onChange: (value) => {
                  setStatusFilter(value)
                  setCurrentPage(1)
                },
              },
              customFilters: [
                {
                  id: 'type-filter',
                  label: 'Type',
                  value: typeFilter,
                  options: typeOptions,
                  onChange: (value) => {
                    setTypeFilter(value)
                    setCurrentPage(1)
                  },
                },
                {
                  id: 'confidentiality-filter',
                  label: 'Confidentiality',
                  value: confidentialityFilter,
                  options: confidentialityOptions,
                  onChange: (value) => {
                    setConfidentialityFilter(value)
                    setCurrentPage(1)
                  },
                },
              ],
              onClearFilters: () => {
                setSearchValue('')
                setStatusFilter('')
                setTypeFilter('')
                setConfidentialityFilter('')
                setCurrentPage(1)
              },
            }}
            emptyMessage="No documents found"
          />
        )}
      </div>
    </AppLayout>
  )
}
