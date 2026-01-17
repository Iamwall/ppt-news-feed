import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { 
  Newspaper, 
  Clock, 
  Trash2,
  FileText,
  Loader2,
  Plus
} from 'lucide-react'
import { format } from 'date-fns'
import { digestsApi } from '../api/client'

import StatusBadge from '../components/StatusBadge'
import { Digest } from '../types'

export default function Digests() {
  const queryClient = useQueryClient()
  
  const { data, isLoading } = useQuery({
    queryKey: ['digests'],
    queryFn: () => digestsApi.list({ limit: 50 }),
  })
  
  const deleteMutation = useMutation({
    mutationFn: (id: number) => digestsApi.delete(id),
    onSuccess: () => {
      toast.success('Digest deleted')
      queryClient.invalidateQueries({ queryKey: ['digests'] })
    },
    onError: () => {
      toast.error('Failed to delete digest')
    },
  })
  
  const digests = (data?.data?.digests || []) as Digest[]
  
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-semibold text-ink-50">
            Digests
          </h1>
          <p className="text-ink-400 mt-1">
            Your curated paper collections with AI summaries
          </p>
        </div>
        
        <Link to="/papers" className="btn-primary">
          <Plus className="w-4 h-4" />
          New Digest
        </Link>
      </div>
      
      {/* Digests List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-science-500 animate-spin" />
        </div>
      ) : digests.length === 0 ? (
        <div className="card p-12 text-center">
          <Newspaper className="w-12 h-12 text-ink-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-ink-300 mb-2">
            No digests yet
          </h3>
          <p className="text-ink-500 mb-4">
            Select papers and create your first digest
          </p>
          <Link to="/papers" className="btn-primary">
            <FileText className="w-4 h-4" />
            Browse Papers
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {digests.map((digest) => (
            <div 
              key={digest.id}
              className="card p-5 hover:border-ink-600 transition-colors group"
            >
              <div className="flex items-start justify-between">
                <Link to={`/digests/${digest.id}`} className="flex-1 min-w-0">
                  <h3 className="font-display text-lg font-medium text-ink-100 group-hover:text-science-400 transition-colors">
                    {digest.name}
                  </h3>
                  
                  <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-ink-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {format(new Date(digest.created_at), 'MMM d, yyyy HH:mm')}
                    </span>
                    <span className="flex items-center gap-1">
                      <FileText className="w-3.5 h-3.5" />
                      {digest.digest_papers?.length || 0} papers
                    </span>
                    <span className="text-ink-500">
                      {digest.ai_provider} / {digest.ai_model}
                    </span>
                  </div>
                  
                  {digest.intro_text && (
                    <p className="text-ink-400 text-sm mt-3 line-clamp-2">
                      {digest.intro_text}
                    </p>
                  )}
                </Link>
                
                <div className="flex items-center gap-3 ml-4">
                  <StatusBadge status={digest.status} />
                  
                  <button
                    onClick={(e) => {
                      e.preventDefault()
                      if (confirm('Delete this digest?')) {
                        deleteMutation.mutate(digest.id)
                      }
                    }}
                    className="text-ink-500 hover:text-accent-400 transition-colors p-2"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
