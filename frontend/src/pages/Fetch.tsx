import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { 
  Download, 
  Loader2, 
  CheckCircle,
  Database,
  Search,
  Calendar,
  Hash
} from 'lucide-react'
import { fetchApi } from '../api/client'

const SOURCES = [
  { id: 'pubmed', name: 'PubMed', description: 'Biomedical and life sciences' },
  { id: 'arxiv', name: 'arXiv', description: 'Physics, math, CS, biology preprints' },
  { id: 'biorxiv', name: 'bioRxiv', description: 'Biology preprints' },
  { id: 'medrxiv', name: 'medRxiv', description: 'Medical preprints' },
  { id: 'semantic_scholar', name: 'Semantic Scholar', description: 'Cross-discipline with citations' },
  { id: 'nature_rss', name: 'Nature RSS', description: 'Nature journal feed' },
  { id: 'science_rss', name: 'Science RSS', description: 'Science journal feed' },
]

export default function Fetch() {
  const queryClient = useQueryClient()
  const [selectedSources, setSelectedSources] = useState<Set<string>>(
    new Set(['pubmed', 'arxiv'])
  )
  const [keywords, setKeywords] = useState('')
  const [maxResults, setMaxResults] = useState(50)
  const [daysBack, setDaysBack] = useState(7)
  const [activeJobId, setActiveJobId] = useState<number | null>(null)
  
  const startFetchMutation = useMutation({
    mutationFn: (data: {
      sources: string[]
      keywords?: string[]
      max_results: number
      days_back: number
    }) => fetchApi.start(data),
    onSuccess: (response) => {
      setActiveJobId(response.data.job_id)
      toast.success('Fetch started!')
    },
    onError: () => {
      toast.error('Failed to start fetch')
    },
  })
  
  // Poll for job status
  const { data: jobStatus } = useQuery({
    queryKey: ['fetchStatus', activeJobId],
    queryFn: () => fetchApi.status(activeJobId!),
    enabled: activeJobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status
      return status === 'completed' || status === 'failed' ? false : 2000
    },
  })
  
  // Handle job completion
  useEffect(() => {
    if (jobStatus?.data?.status === 'completed') {
      toast.success(`Fetched ${jobStatus.data.papers_new} new papers!`)
      queryClient.invalidateQueries({ queryKey: ['papers'] })
      setActiveJobId(null)
    } else if (jobStatus?.data?.status === 'failed') {
      toast.error('Fetch failed. Check the errors.')
      setActiveJobId(null)
    }
  }, [jobStatus?.data?.status, jobStatus?.data?.papers_new, queryClient])
  
  const toggleSource = (sourceId: string) => {
    setSelectedSources(prev => {
      const next = new Set(prev)
      if (next.has(sourceId)) {
        next.delete(sourceId)
      } else {
        next.add(sourceId)
      }
      return next
    })
  }
  
  const handleFetch = () => {
    if (selectedSources.size === 0) {
      toast.error('Select at least one source')
      return
    }
    
    const keywordList = keywords
      .split(',')
      .map(k => k.trim())
      .filter(k => k.length > 0)
    
    startFetchMutation.mutate({
      sources: Array.from(selectedSources),
      keywords: keywordList.length > 0 ? keywordList : undefined,
      max_results: maxResults,
      days_back: daysBack,
    })
  }
  
  const isRunning = startFetchMutation.isPending || activeJobId !== null
  
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-semibold text-ink-50">
          Fetch Papers
        </h1>
        <p className="text-ink-400 mt-1">
          Collect recent papers from scientific databases
        </p>
      </div>
      
      {/* Status Card */}
      {/* Status Card */}
      {isRunning && (
        <div className="card p-6 border-science-600/30 bg-science-950/20">
          {!jobStatus?.data ? (
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-science-600/20 flex items-center justify-center">
                <Loader2 className="w-6 h-6 text-science-400 animate-spin" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-ink-100">
                  Starting fetch...
                </h3>
                <p className="text-sm text-ink-400">
                  Initializing background job...
                </p>
              </div>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-science-600/20 flex items-center justify-center">
                  <Loader2 className="w-6 h-6 text-science-400 animate-spin" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-ink-100">
                    Fetching papers...
                  </h3>
                  <p className="text-sm text-ink-400">
                    {jobStatus.data.current_source && (
                      <span>Processing {jobStatus.data.current_source}... </span>
                    )}
                    {jobStatus.data.papers_fetched} papers fetched
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-semibold text-science-400">
                    {jobStatus.data.progress}%
                  </div>
                </div>
              </div>
              
              {/* Progress bar */}
              <div className="mt-4 h-2 bg-ink-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-science-500 transition-all duration-300"
                  style={{ width: `${jobStatus.data.progress}%` }}
                />
              </div>
            </>
          )}
        </div>
      )}
      
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Sources */}
        <div className="lg:col-span-2">
          <div className="card p-6">
            <h2 className="font-medium text-ink-100 mb-4 flex items-center gap-2">
              <Database className="w-5 h-5 text-science-400" />
              Select Sources
            </h2>
            
            <div className="grid sm:grid-cols-2 gap-3">
              {SOURCES.map(source => (
                <button
                  key={source.id}
                  onClick={() => toggleSource(source.id)}
                  disabled={isRunning}
                  className={`p-4 rounded-lg border text-left transition-all ${
                    selectedSources.has(source.id)
                      ? 'border-science-500 bg-science-950/30'
                      : 'border-ink-700 hover:border-ink-600 bg-ink-800/50'
                  } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-ink-100">
                      {source.name}
                    </span>
                    {selectedSources.has(source.id) && (
                      <CheckCircle className="w-4 h-4 text-science-400" />
                    )}
                  </div>
                  <p className="text-sm text-ink-400">
                    {source.description}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>
        
        {/* Filters */}
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="font-medium text-ink-100 mb-4 flex items-center gap-2">
              <Search className="w-5 h-5 text-science-400" />
              Keywords
            </h2>
            
            <textarea
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="e.g., machine learning, genomics, climate change"
              className="input min-h-[100px] resize-none"
              disabled={isRunning}
            />
            <p className="text-xs text-ink-500 mt-2">
              Comma-separated. Leave empty for recent papers in any field.
            </p>
          </div>
          
          <div className="card p-6">
            <h2 className="font-medium text-ink-100 mb-4 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-science-400" />
              Time Range
            </h2>
            
            <label className="label">Days Back</label>
            <select
              value={daysBack}
              onChange={(e) => setDaysBack(Number(e.target.value))}
              className="input"
              disabled={isRunning}
            >
              <option value={1}>Last 24 hours</option>
              <option value={3}>Last 3 days</option>
              <option value={7}>Last week</option>
              <option value={14}>Last 2 weeks</option>
              <option value={30}>Last month</option>
            </select>
          </div>
          
          <div className="card p-6">
            <h2 className="font-medium text-ink-100 mb-4 flex items-center gap-2">
              <Hash className="w-5 h-5 text-science-400" />
              Max Results
            </h2>
            
            <input
              type="number"
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              min={10}
              max={500}
              className="input"
              disabled={isRunning}
            />
            <p className="text-xs text-ink-500 mt-2">
              Per source. Total may be higher.
            </p>
          </div>
          
          <button
            onClick={handleFetch}
            disabled={isRunning || selectedSources.size === 0}
            className="btn-primary w-full justify-center py-3"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Fetching...
              </>
            ) : (
              <>
                <Download className="w-5 h-5" />
                Start Fetch
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
