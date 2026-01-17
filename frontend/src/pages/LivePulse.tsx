import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { useState, useEffect, useRef } from 'react'
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
} from 'lucide-react'
import { useBranding } from '../contexts/BrandingContext'
import { api } from '../api/client'

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
  const lastFetchTime = useRef<string | null>(null)

  // Fetch feed
  const {
    data: feed,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['pulse-feed', activeDomainId, breakingOnly, validatedOnly],
    queryFn: async () => {
      const response = await api.get('/pulse/feed', {
        params: {
          domain_id: activeDomainId,
          limit: 50,
          breaking_only: breakingOnly,
          passed_triage_only: true,
          validated_only: validatedOnly,
        },
      })
      return response.data as PulsePaper[]
    },
    refetchInterval: autoRefresh ? 30000 : false, // Refresh every 30 seconds if enabled
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['pulse-stats', activeDomainId],
    queryFn: async () => {
      const response = await api.get('/pulse/stats', {
        params: { domain_id: activeDomainId, hours_back: 24 },
      })
      return response.data as FeedStats
    },
    refetchInterval: 60000, // Refresh stats every minute
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
    refetchInterval: autoRefresh ? 15000 : false, // Check breaking every 15 seconds
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [breaking])

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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
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
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            <Radio
              className={`w-4 h-4 ${autoRefresh ? 'animate-pulse' : ''}`}
            />
            {autoRefresh ? 'Live' : 'Paused'}
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
        <div className="grid grid-cols-4 gap-4">
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

      {/* Breaking News Banner */}
      {breaking && breaking.length > 0 && (
        <div className="bg-red-600 text-white rounded-lg p-4">
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

      {/* Filter Bar */}
      <div className="flex items-center gap-4 bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
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
          Showing {feed?.length || 0} items
        </span>
      </div>

      {/* Feed */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : feed && feed.length > 0 ? (
        <div className="space-y-3">
          {feed.map((item) => (
            <div
              key={item.id}
              className={`p-4 bg-white dark:bg-gray-800 rounded-lg border ${
                item.is_breaking
                  ? 'border-red-300 dark:border-red-700 ring-1 ring-red-200'
                  : 'border-gray-200 dark:border-gray-700'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {item.is_breaking && (
                      <span className="px-2 py-0.5 text-xs font-bold bg-red-600 text-white rounded">
                        BREAKING ({Math.round((item.breaking_score || 0) * 100)}%)
                      </span>
                    )}
                    {item.is_validated_source && (
                        <span className="px-2 py-0.5 text-xs font-bold bg-green-100 text-green-700 rounded border border-green-200">
                            VALIDATED
                        </span>
                    )}

                    <span className="text-sm text-gray-500">{item.source}</span>
                    <span className="text-gray-300">•</span>
                    <span className="text-sm text-gray-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTime(item.fetched_at)}
                    </span>
                    {getScoreBadge(item.freshness_score)}
                  </div>

                  <h3 className="font-medium text-lg">
                    {item.url ? (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-primary flex items-center gap-1"
                      >
                        {item.title}
                        <ExternalLink className="w-4 h-4 opacity-50" />
                      </a>
                    ) : (
                      item.title
                    )}
                  </h3>

                  {item.abstract && (
                    <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm line-clamp-2">
                      {item.abstract}
                    </p>
                  )}

                  {item.breaking_keywords && item.breaking_keywords.length > 0 && (
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

                <div className="text-right">
                  {item.breaking_score && (
                    <div className="flex items-center gap-1 text-sm">
                      <TrendingUp className="w-4 h-4 text-red-500" />
                      <span className="text-red-600 font-medium">
                        {Math.round(item.breaking_score * 100)}%
                      </span>
                    </div>
                  )}
                  {item.triage_score && (
                    <div className="text-xs text-gray-500 mt-1">
                      Quality: {Math.round(item.triage_score * 100)}%
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <Radio className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            No items in feed
          </h3>
          <p className="text-gray-500 mt-1">
            {breakingOnly
              ? 'No breaking news at the moment'
              : 'Fetch some content to see the live feed'}
          </p>
        </div>
      )}
    </div>
  )
}
