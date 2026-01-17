import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { 
  FileText, 
  Search, 
  Newspaper,
  CheckSquare,
  Square,
  Loader2
} from 'lucide-react'
import { papersApi, digestsApi } from '../api/client'
import PaperCard from '../components/PaperCard'
import { Paper } from '../types'

export default function Papers() {
  const queryClient = useQueryClient()
  const [selectedPapers, setSelectedPapers] = useState<Set<number>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [minCredibility, setMinCredibility] = useState<number | null>(null)
  const [digestName, setDigestName] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  
  const { data, isLoading } = useQuery({
    queryKey: ['papers', { source: sourceFilter, min_credibility: minCredibility }],
    queryFn: () => papersApi.list({ 
      limit: 100,
      source: sourceFilter || undefined,
      min_credibility: minCredibility || undefined,
    }),
  })
  
  const createDigestMutation = useMutation({
    mutationFn: (data: { name: string; paper_ids: number[] }) => 
      digestsApi.create(data),
    onSuccess: () => {
      toast.success('Digest created! Processing in background...')
      setShowCreateModal(false)
      setSelectedPapers(new Set())
      setDigestName('')
      queryClient.invalidateQueries({ queryKey: ['digests'] })
    },
    onError: () => {
      toast.error('Failed to create digest')
    },
  })
  
  const papers = (data?.data?.papers || []) as Paper[]
  
  // Filter by search query
  const filteredPapers = papers.filter(paper => {
    if (!searchQuery) return true
    const searchLower = searchQuery.toLowerCase()
    return (
      paper.title.toLowerCase().includes(searchLower) ||
      paper.abstract?.toLowerCase().includes(searchLower) ||
      paper.journal?.toLowerCase().includes(searchLower)
    )
  })
  
  const toggleSelect = (id: number) => {
    setSelectedPapers(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }
  
  const toggleSelectAll = () => {
    if (selectedPapers.size === filteredPapers.length) {
      setSelectedPapers(new Set())
    } else {
      setSelectedPapers(new Set(filteredPapers.map(p => p.id)))
    }
  }
  
  const handleCreateDigest = () => {
    if (!digestName.trim()) {
      toast.error('Please enter a digest name')
      return
    }
    
    createDigestMutation.mutate({
      name: digestName,
      paper_ids: Array.from(selectedPapers),
    })
  }
  
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-semibold text-ink-50">
            Papers
          </h1>
          <p className="text-ink-400 mt-1">
            {data?.data?.total || 0} papers in your library
          </p>
        </div>
        
        {selectedPapers.size > 0 && (
          <button 
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            <Newspaper className="w-4 h-4" />
            Create Digest ({selectedPapers.size})
          </button>
        )}
      </div>
      
      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-500" />
              <input
                type="text"
                placeholder="Search papers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>
          
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="input w-48"
          >
            <option value="">All Sources</option>
            <option value="pubmed">PubMed</option>
            <option value="arxiv">arXiv</option>
            <option value="biorxiv">bioRxiv</option>
            <option value="medrxiv">medRxiv</option>
            <option value="semantic_scholar">Semantic Scholar</option>
            <option value="nature_rss">Nature</option>
            <option value="science_rss">Science</option>
          </select>
          
          <select
            value={minCredibility || ''}
            onChange={(e) => setMinCredibility(e.target.value ? Number(e.target.value) : null)}
            className="input w-48"
          >
            <option value="">Any Credibility</option>
            <option value="70">High (70+)</option>
            <option value="50">Moderate (50+)</option>
            <option value="30">Low (30+)</option>
          </select>
          
          <button
            onClick={toggleSelectAll}
            className="btn-secondary"
          >
            {selectedPapers.size === filteredPapers.length ? (
              <>
                <CheckSquare className="w-4 h-4" />
                Deselect All
              </>
            ) : (
              <>
                <Square className="w-4 h-4" />
                Select All
              </>
            )}
          </button>
        </div>
      </div>
      
      {/* Papers List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-science-500 animate-spin" />
        </div>
      ) : filteredPapers.length === 0 ? (
        <div className="card p-12 text-center">
          <FileText className="w-12 h-12 text-ink-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-ink-300 mb-2">
            No papers found
          </h3>
          <p className="text-ink-500">
            {searchQuery || sourceFilter ? 
              'Try adjusting your filters' : 
              'Fetch papers from scientific databases to get started'
            }
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredPapers.map((paper) => (
            <PaperCard 
              key={paper.id} 
              paper={paper} 
              selected={selectedPapers.has(paper.id)}
              onSelect={toggleSelect}
              showCheckbox
            />
          ))}
        </div>
      )}
      
      {/* Create Digest Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-ink-950/80 flex items-center justify-center z-50">
          <div className="card p-6 w-full max-w-md animate-fade-in">
            <h2 className="font-display text-xl font-medium text-ink-50 mb-4">
              Create Digest
            </h2>
            
            <p className="text-ink-400 text-sm mb-4">
              Create a new digest from {selectedPapers.size} selected papers. 
              AI will generate summaries and credibility analysis.
            </p>
            
            <div className="mb-6">
              <label className="label">Digest Name</label>
              <input
                type="text"
                value={digestName}
                onChange={(e) => setDigestName(e.target.value)}
                placeholder="e.g., Weekly Science Roundup"
                className="input"
              />
            </div>
            
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateDigest}
                disabled={createDigestMutation.isPending}
                className="btn-primary"
              >
                {createDigestMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Newspaper className="w-4 h-4" />
                    Create Digest
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
