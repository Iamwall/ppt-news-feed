import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { 
  Mail, 
  Clock, 
  FileText,
  Loader2,
  Edit3,
  Send,
  Download,
  CheckCircle
} from 'lucide-react'
import { format } from 'date-fns'
import { digestsApi } from '../api/client'
import { Digest } from '../types'

export default function Newsletters() {
  const { data, isLoading } = useQuery({
    queryKey: ['digests', 'completed'],
    queryFn: () => digestsApi.list({ limit: 50, status: 'completed' }),
  })
  
  const digests = (data?.data?.digests || []) as Digest[]
  
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-semibold text-ink-50">
          Newsletters
        </h1>
        <p className="text-ink-400 mt-1">
          Edit and format digests before publishing to readers
        </p>
      </div>
      
      {/* Newsletter List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-science-500 animate-spin" />
        </div>
      ) : digests.length === 0 ? (
        <div className="card p-12 text-center">
          <Mail className="w-12 h-12 text-ink-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-ink-300 mb-2">
            No newsletters ready
          </h3>
          <p className="text-ink-500 mb-4">
            Complete a digest first to create a newsletter
          </p>
          <Link to="/digests" className="btn-primary">
            <FileText className="w-4 h-4" />
            View Digests
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {digests.map((digest) => (
            <div 
              key={digest.id}
              className="card p-5 hover:border-ink-600 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <h3 className="font-display text-lg font-medium text-ink-100">
                      {digest.name}
                    </h3>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-ink-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {format(new Date(digest.created_at), 'MMM d, yyyy')}
                    </span>
                    <span className="flex items-center gap-1">
                      <FileText className="w-3.5 h-3.5" />
                      {digest.digest_papers?.length || 0} papers
                    </span>
                  </div>
                  
                  {digest.intro_text && (
                    <p className="text-ink-400 text-sm mt-3 line-clamp-2">
                      {digest.intro_text}
                    </p>
                  )}
                </div>
                
                <div className="flex items-center gap-2 ml-4">
                  <Link
                    to={`/newsletters/${digest.id}/edit`}
                    className="btn-secondary text-sm py-2 px-3"
                  >
                    <Edit3 className="w-4 h-4" />
                    Edit
                  </Link>
                  <Link
                    to={`/newsletters/${digest.id}/edit`}
                    className="btn-primary text-sm py-2 px-3"
                  >
                    <Send className="w-4 h-4" />
                    Publish
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
