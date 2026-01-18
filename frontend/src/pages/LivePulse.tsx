import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { useState, useEffect, useRef, useCallback } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import {
  Zap,
  AlertTriangle,
  Clock,
  RefreshCw,
  Filter,
  ExternalLink,
  Loader2,
  Radio,
  TrendingUp,
  Bell,
  BellOff,
  DownloadCloud,
  LayoutList,
  AlignJustify,
  Keyboard,
} from 'lucide-react'
import { useBranding } from '../contexts/BrandingContext'
import { api } from '../api/client'
import { FetchModal } from '../components/FetchModal'
import { useLiveFeed } from '../hooks/useLiveFeed'

interface PulsePaper {
  id: number
  title: string
  abstract: string | null
  source: string
  url: string | null
  published_date: string | null
  is_breaking: boolean
  breaking_score: number | null
  breaking_keywords: string[] | null
  freshness_score: number | null
  triage_status: string | null
  triage_score: number | null
  is_validated_source?: boolean
  fetched_at: string
}

interface FeedStats {
  time_window_hours: number
  total_papers: number
  breaking_count: number
  passed_triage_count: number
  avg_freshness_score: number
  breaking_rate: number
}

export default function LivePulse() {
  const queryClient = useQueryClient()
  const { activeDomainId } = useBranding()
  const [breakingOnly, setBreakingOnly] = useState(false)
  const [validatedOnly, setValidatedOnly] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [showBreakingAlert, setShowBreakingAlert] = useState(true)
  const [showFetchModal, setShowFetchModal] = useState(false)
  
  // Tactical Mode State
  const [denseMode, setDenseMode] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  
  const lastFetchTime = useRef<string | null>(null)
  const parentRef = useRef<HTMLDivElement>(null)

  // WebSocket Live Feed
  const { status: wsStatus } = useLiveFeed({
    domainId: activeDomainId,
    active: autoRefresh,
    onNewItem: () => {
        // If we want to auto-select new items, logic would go here
        // For now, we keep selection stable
    }
  })

  // Fetch feed (initial load)
  const {
    data: feed,
    isLoading,
  } = useQuery({
    queryKey: ['pulse-feed', activeDomainId, breakingOnly, validatedOnly],
    queryFn: async () => {
      const response = await api.get('/pulse/feed', {
        params: {
          domain_id: activeDomainId,
          limit: 200, 
          breaking_only: breakingOnly,
          passed_triage_only: true,
          validated_only: validatedOnly,
        },
      })
      return response.data as PulsePaper[]
    },
    refetchInterval: autoRefresh && wsStatus !== 'connected' ? 30000 : false,
  })

  // Virtualizer
  const rowVirtualizer = useVirtualizer({
    count: feed?.length || 0,
    getScrollElement: () => parentRef.current,
    estimateSize: () => denseMode ? 80 : 200, 
    overscan: 5,
  })

  // Scroll to selected index
  useEffect(() => {
    if (selectedIndex !== null && feed && selectedIndex < feed.length) {
      rowVirtualizer.scrollToIndex(selectedIndex, { align: 'center' })
    }
  }, [selectedIndex, rowVirtualizer, feed])

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
        // Ignore if typing in inputs
        if ((e.target as HTMLElement).tagName === 'INPUT' || (e.target as HTMLElement).tagName === 'TEXTAREA') return

        if (!feed || feed.length === 0) return

        switch(e.key) {
            case 'j': // Next
                e.preventDefault()
                setSelectedIndex(prev => {
                    const next = (prev === null) ? 0 : Math.min(prev + 1, feed.length - 1)
                    return next
                })
                break
            case 'k': // Prev
                e.preventDefault()
                setSelectedIndex(prev => {
                    const next = (prev === null) ? 0 : Math.max(prev - 1, 0)
                    return next
                })
                break
            case 'o': // Open
            case 'Enter':
                e.preventDefault()
                if (selectedIndex !== null) {
                    const paper = feed[selectedIndex]
                    if (paper.url) window.open(paper.url, '_blank')
                }
                break
            case 'x': // Discard (simulated for now)
                e.preventDefault()
                if (selectedIndex !== null) {
                    // Logic to mark as 'read' or remove would go here
                    toast('Discarded (Simulation)', { icon: '🗑️', position: 'bottom-right' })
                }
                break
             case 'Escape':
                setSelectedIndex(null)
                break
        }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [feed, selectedIndex])


  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['pulse-stats', activeDomainId],
    queryFn: async () => {
      const response = await api.get('/pulse/stats', {
        params: { domain_id: activeDomainId, hours_back: 24 },
      })
      return response.data as FeedStats
    },
    refetchInterval: 60000, 
  })

  // Fetch breaking news
  const { data: breaking } = useQuery({
    queryKey: ['pulse-breaking', activeDomainId],
    queryFn: async () => {
      const response = await api.get('/pulse/breaking', {
        params: { domain_id: activeDomainId, limit: 5 },
      })
      return response.data as PulsePaper[]
    },
    refetchInterval: autoRefresh ? 15000 : false, 
  })

  // Refresh scores mutation
  const refreshMutation = useMutation({
    mutationFn: () =>
      api.post('/pulse/refresh', null, {
        params: { domain_id: activeDomainId, hours_back: 48 },
      }),
    onSuccess: (response) => {
      const data = response.data
      toast.success(
        `Refreshed ${data.papers_updated} papers, ${data.new_breaking} new breaking`
      )
      queryClient.invalidateQueries({ queryKey: ['pulse-feed'] })
      queryClient.invalidateQueries({ queryKey: ['pulse-breaking'] })
      queryClient.invalidateQueries({ queryKey: ['pulse-stats'] })
    },
    onError: () => {
      toast.error('Failed to refresh scores')
    },
  })

  // Check for new breaking news
  useEffect(() => {
    if (breaking && breaking.length > 0 && showBreakingAlert) {
      const latestBreaking = breaking[0]
      if (
        lastFetchTime.current &&
        new Date(latestBreaking.fetched_at) > new Date(lastFetchTime.current)
      ) {
        toast.custom(
          (t) => (
            <div
              className={`${
                t.visible ? 'animate-enter' : 'animate-leave'
              } max-w-md w-full bg-red-600 text-white shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5`}
            >
              <div className="flex-1 w-0 p-4">
                <div className="flex items-start">
                  <AlertTriangle className="w-6 h-6 flex-shrink-0" />
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-medium">BREAKING NEWS</p>
                    <p className="mt-1 text-sm opacity-90">
                      {latestBreaking.title}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ),
          { duration: 5000 }
        )
      }
      lastFetchTime.current = new Date().toISOString()
    }
  }, [breaking, showBreakingAlert])

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  const getFreshnessColor = (score: number | null) => {
    if (!score) return 'text-gray-400'
    if (score >= 0.8) return 'text-green-500'
    if (score >= 0.5) return 'text-yellow-500'
    if (score >= 0.3) return 'text-orange-500'
    return 'text-red-500'
  }

  const getScoreBadge = (score: number | null) => {
    if (!score) return null
    const percentage = Math.round(score * 100)
    return (
      <span
        className={`text-xs font-medium ${getFreshnessColor(score)}`}
        title={`Freshness: ${percentage}%`}
      >
        {percentage}%
      </span>
    )
  }

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col space-y-4">
      {/* Header */}
      <div className="flex-none flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Radio className="w-7 h-7 text-red-500" />
            Live Pulse
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Real-time feed with breaking news detection
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-500 mr-2">
            <Keyboard className="w-3 h-3" />
            <span>j/k to nav</span>
            <span>o to open</span>
          </div>
          <button
            onClick={() => setShowBreakingAlert(!showBreakingAlert)}
            className={`p-2 rounded-lg ${
              showBreakingAlert
                ? 'bg-red-100 text-red-600'
                : 'bg-gray-100 text-gray-500'
            }`}
            title={showBreakingAlert ? 'Alerts on' : 'Alerts off'}
          >
            {showBreakingAlert ? (
              <Bell className="w-5 h-5" />
            ) : (
              <BellOff className="w-5 h-5" />
            )}
          </button>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
              autoRefresh
                ? wsStatus === 'connected'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-amber-100 text-amber-700'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            <Radio
              className={`w-4 h-4 ${
                autoRefresh
                  ? wsStatus === 'connected'
                    ? 'text-green-600 animate-pulse'
                    : 'text-amber-500' // Connecting/Retry
                  : 'text-gray-400'
              }`}
            />
            {autoRefresh ? (wsStatus === 'connected' ? 'Live' : 'Connecting...') : 'Paused'}
          </button>
          <button
            onClick={() => setShowFetchModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
             <DownloadCloud className="w-4 h-4" />
             Fetch Content
          </button>
          <button
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
          >
            {refreshMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Refresh Scores
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="flex-none grid grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500">Total (24h)</div>
            <div className="text-2xl font-bold">{stats.total_papers}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-red-200 dark:border-red-800">
            <div className="text-sm text-gray-500 flex items-center gap-1">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              Breaking
            </div>
            <div className="text-2xl font-bold text-red-600">
              {stats.breaking_count}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-green-200 dark:border-green-800">
            <div className="text-sm text-gray-500">Passed Triage</div>
            <div className="text-2xl font-bold text-green-600">
              {stats.passed_triage_count}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500">Avg Freshness</div>
            <div
              className={`text-2xl font-bold ${getFreshnessColor(
                stats.avg_freshness_score
              )}`}
            >
              {Math.round(stats.avg_freshness_score * 100)}%
            </div>
          </div>
        </div>
      )}

      {/* Breaking News Banner - Only show if not in dense mode to save space, or make it smaller */}
      {!denseMode && breaking && breaking.length > 0 && (
        <div className="flex-none bg-red-600 text-white rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5" />
            <span className="font-bold">BREAKING NEWS</span>
          </div>
          <div className="space-y-2">
            {breaking.slice(0, 3).map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between bg-red-700/50 rounded p-2"
              >
                <div className="flex-1">
                  <a
                    href={item.url || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline font-medium"
                  >
                    {item.title}
                  </a>
                  <div className="text-sm opacity-75 mt-1">
                    {item.source} • {formatTime(item.fetched_at)}
                  </div>
                </div>
                {item.breaking_score && (
                  <div className="text-sm bg-red-800 px-2 py-1 rounded">
                    {Math.round(item.breaking_score * 100)}% urgency
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Toolbar */}
      <div className="flex-none flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-4">
            <Filter className="w-5 h-5 text-gray-400" />
            <label className="flex items-center gap-2">
            <input
                type="checkbox"
                checked={breakingOnly}
                onChange={(e) => setBreakingOnly(e.target.checked)}
                className="rounded"
            />
            <span className="text-sm">Breaking only</span>
            </label>
            <label className="flex items-center gap-2 ml-2">
                <input
                    type="checkbox"
                    checked={validatedOnly}
                    onChange={(e) => setValidatedOnly(e.target.checked)}
                    className="rounded"
                />
                <span className="text-sm flex items-center gap-1">Validated only</span>
            </label>
            <span className="text-gray-300">|</span>
            <span className="text-sm text-gray-500">
            {feed?.length || 0} items
            </span>
        </div>
        
        {/* Dense Mode Toggle */}
        <div className="flex items-center gap-2 border-l pl-4 border-gray-200 dark:border-gray-700">
            <button
                onClick={() => setDenseMode(false)}
                className={`p-1.5 rounded ${!denseMode ? 'bg-gray-100 text-gray-900' : 'text-gray-400 hover:text-gray-600'}`}
                title="Comfortable View"
            >
                <LayoutList className="w-5 h-5" />
            </button>
            <button
                onClick={() => setDenseMode(true)}
                className={`p-1.5 rounded ${denseMode ? 'bg-gray-100 text-gray-900' : 'text-gray-400 hover:text-gray-600'}`}
                title="Dense View"
            >
                <AlignJustify className="w-5 h-5" />
            </button>
        </div>
      </div>

      {/* Feed (Virtualized) */}
      <div 
        ref={parentRef} 
        className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
      >
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : feed && feed.length > 0 ? (
          <div
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualItem) => {
              const item = feed[virtualItem.index]
              const isSelected = selectedIndex === virtualItem.index
              return (
                <div
                  key={item.id}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: `${virtualItem.size}px`,
                    transform: `translateY(${virtualItem.start}px)`,
                  }}
                  className={`px-4 py-2 ${virtualItem.index !== feed.length - 1 ? 'border-b border-gray-200 dark:border-gray-700' : ''}`}
                >
                    <div 
                        onClick={() => setSelectedIndex(virtualItem.index)}
                        className={`h-full flex ${denseMode ? 'items-center' : 'items-start'} gap-4 ${denseMode ? 'py-1' : 'py-3'} cursor-pointer transition-colors rounded-lg px-2 -mx-2 ${
                        isSelected 
                            ? 'bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-500' 
                            : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                        } ${
                            item.is_breaking && !isSelected ? 'bg-red-50/50 dark:bg-red-900/10' : ''
                        }`}
                    >
                        <div className="flex-1 min-w-0">
                             <div className="flex items-center gap-2 mb-1">
                                {item.is_breaking && (
                                <span className={`flex-shrink-0 ${denseMode ? 'w-2 h-2 rounded-full bg-red-600' : 'px-2 py-0.5 text-xs font-bold bg-red-600 text-white rounded'}`}>
                                    {denseMode ? '' : `BREAKING (${Math.round((item.breaking_score || 0) * 100)}%)`}
                                </span>
                                )}
                                {item.is_validated_source && (
                                    <span className="flex-shrink-0 px-1.5 py-0.5 text-[10px] uppercase font-bold bg-green-100 text-green-700 rounded border border-green-200">
                                        VAL
                                    </span>
                                )}

                                <span className="text-xs font-medium text-gray-500 truncate max-w-[150px]">{item.source}</span>
                                <span className="text-gray-300">•</span>
                                <span className="text-xs text-gray-500 flex items-center gap-1 flex-shrink-0">
                                <Clock className="w-3 h-3" />
                                {formatTime(item.fetched_at)}
                                </span>
                            </div>

                            <h3 className={`font-medium ${denseMode ? 'text-sm truncate' : 'text-lg leading-tight'} ${isSelected ? 'text-blue-700 dark:text-blue-300' : ''}`}>
                                {item.url ? (
                                <a
                                    href={item.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="hover:text-primary flex items-center gap-1"
                                >
                                    {item.title}
                                    {!denseMode && <ExternalLink className="w-4 h-4 opacity-50" />}
                                </a>
                                ) : (
                                item.title
                                )}
                            </h3>

                            {!denseMode && item.abstract && (
                                <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm line-clamp-2">
                                {item.abstract}
                                </p>
                            )}

                            {!denseMode && item.breaking_keywords && item.breaking_keywords.length > 0 && (
                                <div className="flex gap-2 mt-2">
                                {item.breaking_keywords.map((kw, i) => (
                                    <span
                                    key={i}
                                    className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded"
                                    >
                                    {kw}
                                    </span>
                                ))}
                                </div>
                            )}
                        </div>

                        <div className="flex-shrink-0 text-right">
                             {item.breaking_score && (
                                <div className="flex items-center justify-end gap-1 text-sm">
                                <TrendingUp className="w-4 h-4 text-red-500" />
                                <span className="text-red-600 font-medium">
                                    {Math.round(item.breaking_score * 100)}%
                                </span>
                                </div>
                            )}
                             <div className="flex items-center justify-end gap-2 mt-1">
                                {getScoreBadge(item.freshness_score)}
                             </div>
                        </div>
                    </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
                <Radio className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    No items in feed
                </h3>
                <p className="text-gray-500 mt-1">
                    {breakingOnly
                    ? 'No breaking news at the moment'
                    : 'Fetch some content to see the live feed'}
                </p>
            </div>
          </div>
        )}
      </div>
      
      <FetchModal isOpen={showFetchModal} onClose={() => setShowFetchModal(false)} />
    </div>
  )
}
