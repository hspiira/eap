/**
 * Admin Password Display Component
 * Displays the admin password returned from tenant creation
 * Matches the requirements from TENANT_CREATION_UI_GUIDE.md
 */

import { useState } from 'react'
import { Eye, EyeOff, Copy, Download } from 'lucide-react'
import type { TenantCreateResponse } from '@/api/endpoints/tenants'

interface AdminPasswordDisplayProps {
  tenant: TenantCreateResponse
  onLogin: () => void
  onDownload: () => void
  onClose: () => void
}

export function AdminPasswordDisplay({ 
  tenant, 
  onLogin, 
  onDownload, 
  onClose 
}: AdminPasswordDisplayProps) {
  const [showPassword, setShowPassword] = useState(false)
  const [copiedEmail, setCopiedEmail] = useState(false)
  const [copiedPassword, setCopiedPassword] = useState(false)

  const copyEmail = () => {
    navigator.clipboard.writeText(tenant.admin_email)
    setCopiedEmail(true)
    setTimeout(() => setCopiedEmail(false), 2000)
  }

  const copyPassword = () => {
    navigator.clipboard.writeText(tenant.admin_password)
    setCopiedPassword(true)
    setTimeout(() => setCopiedPassword(false), 2000)
  }

  return (
    <div className="fixed inset-0 bg-safe/50 flex items-center justify-center z-50 p-4">
      <div className="bg-calm p-8 rounded-none max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-safe mb-2">✓ Tenant Created Successfully!</h2>
          <div className="mb-4 p-3 bg-calm border-[0.5px] border-safe rounded-none">
            <p className="text-safe text-sm font-medium mb-1">Tenant: {tenant.name}</p>
            <p className="text-safe-light text-sm">Code: {tenant.code}</p>
          </div>
        </div>
        
        <div className="mb-6">
          <div className="p-3 bg-nurturing-light border-[0.5px] border-nurturing rounded-none mb-4">
            <p className="text-safe text-sm font-medium">
              ⚠️ IMPORTANT: Save These Credentials
            </p>
            <p className="text-safe-light text-xs mt-1">
              These credentials cannot be retrieved later. Please save them securely.
            </p>
          </div>
          
          <div className="mb-4">
            <label className="block text-safe text-sm font-medium mb-2">
              Admin Email
            </label>
            <div className="flex gap-2">
              <div className="flex-1 px-4 py-2 bg-calm border-[0.5px] border-safe rounded-none">
                <code className="text-safe">{tenant.admin_email}</code>
              </div>
              <button
                onClick={copyEmail}
                className="px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors flex items-center gap-2"
                title="Copy email"
              >
                <Copy size={16} />
                {copiedEmail ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-safe text-sm font-medium mb-2">
              Admin Password
            </label>
            <div className="flex gap-2">
              <div className="flex-1 px-4 py-2 bg-calm border-[0.5px] border-safe rounded-none flex items-center">
                <code className="text-safe font-mono flex-1">
                  {showPassword ? tenant.admin_password : '•'.repeat(16)}
                </code>
                <button
                  onClick={() => setShowPassword(!showPassword)}
                  className="ml-2 text-safe hover:text-natural transition-colors"
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <button
                onClick={copyPassword}
                className="px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors flex items-center gap-2"
                title="Copy password"
              >
                <Copy size={16} />
                {copiedPassword ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <button
            onClick={onDownload}
            className="w-full py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors flex items-center justify-center gap-2"
          >
            <Download size={16} />
            Download Credentials
          </button>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onLogin}
            className="flex-1 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors"
          >
            Login Now
          </button>
          <button
            onClick={onClose}
            className="flex-1 py-3 bg-nurturing hover:bg-nurturing-dark text-white font-semibold rounded-none transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
