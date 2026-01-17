import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { 
  FileText, 
  Newspaper, 
  TrendingUp, 
  Clock, 
  ArrowRight,
  Download,
  Sparkles
} from 'lucide-react'
import { papersApi, digestsApi } from '../api/client'
import PaperCard from '../components/PaperCard'
import StatusBadge from '../components/StatusBadge'
import { format } from 'date-fns'
import { Paper, Digest } from '../types'

export default function Dashboard() {
  const { data: papersData } = useQuery({
    queryKey: ['papers', { limit: 5 }],
    queryFn: () => papersApi.list({ limit: 5 }),
  })
  
  const { data: digestsData } = useQuery({
    queryKey: ['digests', { limit: 5 }],
    queryFn: () => digestsApi.list({ limit: 5 }),
  })
  
  const papers = (papersData?.data?.papers || []) as Paper[]
  const digests = (digestsData?.data?.digests || []) as Digest[]
  const totalPapers = papersData?.data?.total || 0
  const totalDigests = digestsData?.data?.total || 0
  
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-semibold text-ink-50">
            Dashboard
          </h1>
          <p className="text-ink-400 mt-1">
            Your scientific research command center
          </p>
        </div>
        
        <Link to="/fetch" className="btn-primary">
          <Download className="w-4 h-4" />
          Fetch New Papers
        </Link>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-science-600/20 flex items-center justify-center">
              <FileText className="w-6 h-6 text-science-400" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-ink-50">{totalPapers}</p>
              <p className="text-sm text-ink-400">Papers Collected</p>
            </div>
          </div>
        </div>
        
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-accent-600/20 flex items-center justify-center">
              <Newspaper className="w-6 h-6 text-accent-400" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-ink-50">{totalDigests}</p>
              <p className="text-sm text-ink-400">Digests Created</p>
            </div>
          </div>
        </div>
        
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-yellow-600/20 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-yellow-400" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-ink-50">
                {papers.filter(p => p.credibility_score && p.credibility_score >= 70).length}
              </p>
              <p className="text-sm text-ink-400">High Credibility</p>
            </div>
          </div>
        </div>
        
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-purple-600/20 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-ink-50">
                {papers.filter(p => p.summary_headline).length}
              </p>
              <p className="text-sm text-ink-400">AI Summarized</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Recent Papers */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-xl font-medium text-ink-100">
            Recent Papers
          </h2>
          <Link 
            to="/papers" 
            className="text-sm text-science-400 hover:text-science-300 flex items-center gap-1"
          >
            View all
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        
        {papers.length === 0 ? (
          <div className="card p-12 text-center">
            <FileText className="w-12 h-12 text-ink-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-ink-300 mb-2">
              No papers yet
            </h3>
            <p className="text-ink-500 mb-4">
              Start by fetching papers from scientific databases
            </p>
            <Link to="/fetch" className="btn-primary">
              <Download className="w-4 h-4" />
              Fetch Papers
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {papers.map((paper) => (
              <PaperCard key={paper.id} paper={paper} />
            ))}
          </div>
        )}
      </section>
      
      {/* Recent Digests */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-xl font-medium text-ink-100">
            Recent Digests
          </h2>
          <Link 
            to="/digests" 
            className="text-sm text-science-400 hover:text-science-300 flex items-center gap-1"
          >
            View all
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        
        {digests.length === 0 ? (
          <div className="card p-12 text-center">
            <Newspaper className="w-12 h-12 text-ink-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-ink-300 mb-2">
              No digests yet
            </h3>
            <p className="text-ink-500 mb-4">
              Create a digest to generate AI summaries and newsletters
            </p>
            <Link to="/papers" className="btn-primary">
              <Newspaper className="w-4 h-4" />
              Select Papers
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {digests.map((digest) => (
              <Link 
                key={digest.id}
                to={`/digests/${digest.id}`}
                className="card p-5 hover:border-ink-600 transition-colors group"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-ink-100 group-hover:text-science-400 transition-colors">
                      {digest.name}
                    </h3>
                    <div className="flex items-center gap-4 mt-2 text-sm text-ink-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {format(new Date(digest.created_at), 'MMM d, yyyy')}
                      </span>
                      <span>
                        {digest.digest_papers?.length || 0} papers
                      </span>
                    </div>
                  </div>
                  <StatusBadge status={digest.status} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
