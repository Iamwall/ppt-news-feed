import { ExternalLink, Calendar, Users, FileWarning } from 'lucide-react'
import { format } from 'date-fns'
import clsx from 'clsx'
import CredibilityBadge from './CredibilityBadge'

import { Paper } from '../types'

interface PaperCardProps {
  paper: Paper
  selected?: boolean
  onSelect?: (id: number) => void
  showCheckbox?: boolean
}

export default function PaperCard({ 
  paper, 
  selected, 
  onSelect,
  showCheckbox = false 
}: PaperCardProps) {
  const displayTitle = paper.summary_headline || paper.title
  const displaySummary = paper.summary_takeaway || paper.abstract
  
  return (
    <article 
      className={clsx(
        'card p-5 transition-all duration-200 group',
        selected && 'ring-2 ring-science-500 bg-science-950/30',
        onSelect && 'cursor-pointer hover:border-ink-600'
      )}
      onClick={() => onSelect?.(paper.id)}
    >
      <div className="flex gap-4">
        {/* Checkbox */}
        {showCheckbox && (
          <div className="pt-1">
            <input
              type="checkbox"
              checked={selected}
              onChange={() => onSelect?.(paper.id)}
              className="w-5 h-5 rounded border-ink-600 bg-ink-800 text-science-500 focus:ring-science-500 focus:ring-offset-ink-900"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between gap-4 mb-3">
            <div className="flex-1 min-w-0">
              <h3 className="font-display text-lg font-medium text-ink-50 leading-tight group-hover:text-science-400 transition-colors line-clamp-2">
                {displayTitle}
              </h3>
              
              {/* Meta */}
              <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-ink-400">
                {paper.journal && (
                  <span className="flex items-center gap-1">
                    <span className="text-ink-300">{paper.journal}</span>
                  </span>
                )}
                
                {paper.published_date && (
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    {format(new Date(paper.published_date), 'MMM d, yyyy')}
                  </span>
                )}
                
                {paper.authors.length > 0 && (
                  <span className="flex items-center gap-1">
                    <Users className="w-3.5 h-3.5" />
                    {paper.authors.slice(0, 2).map(a => a.name).join(', ')}
                    {paper.authors.length > 2 && ` +${paper.authors.length - 2}`}
                  </span>
                )}
                
                {paper.is_preprint && (
                  <span className="badge-warning flex items-center gap-1">
                    <FileWarning className="w-3 h-3" />
                    Preprint
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex flex-col items-end gap-2">
              <CredibilityBadge score={paper.credibility_score} size="sm" />
              
              {paper.url && (
                <a
                  href={paper.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="text-ink-400 hover:text-science-400 transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>
          </div>
          
          {/* Summary */}
          {displaySummary && (
            <p className="text-ink-300 text-sm leading-relaxed line-clamp-3 mb-3">
              {displaySummary}
            </p>
          )}
          
          {/* Tags */}
          {paper.tags && paper.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {paper.tags.map((tag, i) => (
                <span 
                  key={i}
                  className="badge-neutral text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
          
          {/* Source badge */}
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs uppercase tracking-wider text-ink-500 font-medium">
              {paper.source.replace('_', ' ')}
            </span>
          </div>
        </div>
      </div>
    </article>
  )
}
