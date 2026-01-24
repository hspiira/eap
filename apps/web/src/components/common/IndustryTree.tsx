/**
 * IndustryTree Component
 * Hierarchical tree view for industries with expand/collapse
 */

import { useState, useMemo } from 'react'
import { ChevronRight, ChevronDown, Folder, FolderOpen } from 'lucide-react'
import type { Industry } from '@/types/entities'

export interface IndustryTreeProps {
  industries: Industry[]
  onSelect?: (industry: Industry) => void
  selectedId?: string | null
  emptyMessage?: string
  className?: string
}

function buildTree(items: Industry[], parentId: string | null = null): Industry[] {
  return items
    .filter((i) => (parentId == null ? !i.parent_id : i.parent_id === parentId))
    .sort((a, b) => (a.name ?? '').localeCompare(b.name ?? ''))
}

export function IndustryTree({
  industries,
  onSelect,
  selectedId,
  emptyMessage = 'No industries',
  className = '',
}: IndustryTreeProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const roots = useMemo(() => buildTree(industries, null), [industries])

  const toggle = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const renderNode = (node: Industry, depth: number) => {
    const children = buildTree(industries, node.id)
    const hasChildren = children.length > 0
    const isExpanded = expanded.has(node.id)
    const isSelected = selectedId === node.id

    return (
      <div key={node.id} className="select-none">
        <div
          style={{ paddingLeft: `${depth * 20 + 8}px` }}
          className={`flex items-center gap-2 py-2 px-2 rounded-none cursor-pointer transition-colors ${
            isSelected ? 'bg-natural text-white' : 'hover:bg-safe-light/10'
          }`}
          onClick={() => onSelect?.(node)}
        >
          <button
            type="button"
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
            className="p-0.5 rounded-none hover:bg-safe-light/20 flex-shrink-0"
            onClick={(e) => {
              e.stopPropagation()
              if (hasChildren) toggle(node.id)
            }}
          >
            {hasChildren ? (
              isExpanded ? (
                <ChevronDown size={16} />
              ) : (
                <ChevronRight size={16} />
              )
            ) : (
              <span className="w-4 inline-block" />
            )}
          </button>
          <span className="flex-shrink-0">
            {hasChildren && isExpanded ? (
              <FolderOpen size={18} className="text-safe-light" />
            ) : (
              <Folder size={18} className="text-safe-light" />
            )}
          </span>
          <span className="font-medium truncate">{node.name}</span>
          {node.code && (
            <span className="text-safe-light text-sm truncate">({node.code})</span>
          )}
        </div>
        {hasChildren && isExpanded && (
          <div>
            {children.map((child) => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  if (roots.length === 0) {
    return (
      <div className={`py-12 text-center text-safe-light ${className}`}>
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className={`border border-[0.5px] border-safe bg-calm ${className}`}>
      {roots.map((node) => renderNode(node, 0))}
    </div>
  )
}
