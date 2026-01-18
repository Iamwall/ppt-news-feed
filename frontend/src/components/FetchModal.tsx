import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { fetchApi } from '../api/client'
import { Loader2, X, DownloadCloud, Check, Globe } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { useBranding } from '../contexts/BrandingContext'

import { Source } from '../types'

interface FetchModalProps {
  isOpen: boolean
  onClose: () => void
}

export function FetchModal({ isOpen, onClose }: FetchModalProps) {
  const { domains, activeDomainId } = useBranding()
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [selectedDomain, setSelectedDomain] = useState<string | null>(activeDomainId)
  const [daysBack, setDaysBack] = useState(7)
  const [maxResults, setMaxResults] = useState(50)

  // Sync selected domain with active domain when modal opens
  useEffect(() => {
    if (isOpen && activeDomainId) {
        setSelectedDomain(activeDomainId)
    }
  }, [isOpen, activeDomainId])

  // Fetch available sources
  const { data: sourcesData, isLoading: isLoadingSources, isError, error } = useQuery({
    queryKey: ['fetch-sources'],
    queryFn: fetchApi.getSources,
    enabled: isOpen,
  })

  // Pre-select all sources when loaded
  useEffect(() => {
    if (sourcesData?.data?.sources) {
      setSelectedSources(sourcesData.data.sources.map((s: Source) => s.id))
    }
  }, [sourcesData])

  const fetchMutation = useMutation({
    mutationFn: fetchApi.start,
    onSuccess: () => {
      toast.success('Fetch job started successfully!')
      onClose()
    },
    onError: (error) => {
      toast.error('Failed to start fetch job')
      console.error(error)
    },
  })

  const handleFetch = () => {
    fetchMutation.mutate({
      sources: selectedSources,
      days_back: daysBack,
      max_results: maxResults,
      domain_id: selectedDomain || undefined,
    })
  }

  const toggleSource = (sourceId: string) => {
    if (selectedSources.includes(sourceId)) {
      setSelectedSources(selectedSources.filter((id) => id !== sourceId))
    } else {
      setSelectedSources([...selectedSources, sourceId])
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg border border-gray-200 dark:border-gray-700 bg-white/95 dark:bg-gray-800/95">
        <div className="flex items-center justify-between p-6 border-b border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <DownloadCloud className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Fetch New Content</h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Crawl sources for latest papers</p>
                </div>
            </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Settings */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="days-back" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Days Back
              </label>
              <input
                id="days-back"
                type="number"
                min="1"
                max="30"
                value={daysBack}
                onChange={(e) => setDaysBack(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <div>
              <label htmlFor="max-results" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Max Results (per source)
              </label>
              <input
                id="max-results"
                type="number"
                min="1"
                max="100"
                value={maxResults}
                onChange={(e) => setMaxResults(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
          </div>

          {/* Domain Selection */}
          {domains.length > 0 && (
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Target Domain
                </label>
                <div className="grid grid-cols-2 gap-2">
                    {domains.map((domain) => (
                        <button
                            key={domain.id}
                            onClick={() => setSelectedDomain(domain.id)}
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-all ${
                                selectedDomain === domain.id
                                    ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500/20'
                                    : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-300'
                            }`}
                        >
                            <Globe className="w-4 h-4" />
                            {domain.name}
                        </button>
                    ))}
                </div>
            </div>
          )}

          {/* Sources List */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Select Sources
            </label>
            {isLoadingSources ? (
              <div className="flex items-center justify-center p-8 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : isError ? (
                <div className="p-4 bg-red-50 dark:bg-red-900/10 text-red-600 dark:text-red-400 rounded-lg text-sm text-center">
                    Failed to load sources. Please try again.
                    <br/>
                    <span className="text-xs opacity-70">{(error as Error)?.message}</span>
                </div>
            ) : !sourcesData?.data?.sources || sourcesData.data.sources.length === 0 ? (
                <div className="p-8 text-center bg-gray-50 dark:bg-gray-900/50 rounded-lg text-gray-500">
                    No sources available.
                </div>
            ) : (
                <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto p-1 custom-scrollbar">
                {sourcesData?.data?.sources?.map((source: Source) => (
                    <button
                    key={source.id}
                    onClick={() => toggleSource(source.id)}
                    className={`flex items-center gap-3 p-3 rounded-lg border text-left transition-all ${
                        selectedSources.includes(source.id)
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                        : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                    >
                    <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                        selectedSources.includes(source.id)
                        ? 'bg-blue-500 border-blue-500'
                        : 'border-gray-300 dark:border-gray-600'
                    }`}>
                        {selectedSources.includes(source.id) && (
                            <Check className="w-3.5 h-3.5 text-white" />
                        )}
                    </div>
                    <div>
                        <div className="font-medium text-sm text-gray-900 dark:text-white">
                            {source.name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                            {source.type}
                        </div>
                    </div>
                    </button>
                ))}
                </div>
            )}
          </div>
        </div>

        <div className="p-6 border-t border-gray-100 dark:border-gray-700 flex justify-end gap-3 bg-gray-50 dark:bg-gray-800/50 rounded-b-xl">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-700 border border-transparent hover:border-gray-200 dark:hover:border-gray-600 rounded-lg transition-all"
          >
            Cancel
          </button>
          <button
            onClick={handleFetch}
            disabled={fetchMutation.isPending || selectedSources.length === 0}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm hover:shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {fetchMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <DownloadCloud className="w-4 h-4" />
            )}
            Start Fetching
          </button>
        </div>
      </div>
    </div>
  )
}
