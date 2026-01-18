import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { useState } from 'react'
import {
  Calendar,
  Plus,
  Trash2,
  Play,
  Pause,
  Clock,
  Loader2,
  XCircle,
  History,
  Zap,
} from 'lucide-react'
import { useBranding } from '../contexts/BrandingContext'
import { api } from '../api/client'

interface DigestSchedule {
  id: number
  domain_id: string
  name: string
  description: string | null
  cron_expression: string
  timezone: string
  is_active: boolean
  lookback_hours: number
  max_items: number
  top_picks_count: number
  cluster_topics: boolean
  min_triage_score: number | null
  only_passed_triage: boolean
  ai_provider: string
  ai_model: string | null
  last_run_at: string | null
  next_run_at: string | null
  run_count: number
  last_error: string | null
  created_at: string
}

interface ScheduledDigest {
  id: number
  schedule_id: number
  digest_id: number
  papers_considered: number
  papers_included: number
  topics_clustered: number
  triggered_at: string
  completed_at: string | null
  generation_time_seconds: number | null
}

// Common cron presets
const CRON_PRESETS = [
  { label: 'Every morning at 6 AM', value: '0 6 * * *' },
  { label: 'Every evening at 6 PM', value: '0 18 * * *' },
  { label: 'Twice daily (6 AM & 6 PM)', value: '0 6,18 * * *' },
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every Monday at 9 AM', value: '0 9 * * 1' },
  { label: 'Custom', value: 'custom' },
]

export default function Schedules() {
  const queryClient = useQueryClient()
  const { activeDomainId } = useBranding()
  const [showAddForm, setShowAddForm] = useState(false)
  const [showHistory, setShowHistory] = useState<number | null>(null)
  const [cronPreset, setCronPreset] = useState('0 6 * * *')
  const [customCron, setCustomCron] = useState('')
  const [newSchedule, setNewSchedule] = useState({
    name: '',
    description: '',
    cron_expression: '0 6 * * *',
    timezone: 'UTC',
    lookback_hours: 24,
    max_items: 10,
    top_picks_count: 3,
    cluster_topics: true,
    ai_provider: 'gemini',
  })

  // Fetch schedules
  const { data: schedules, isLoading } = useQuery({
    queryKey: ['schedules', activeDomainId],
    queryFn: async () => {
      const response = await api.get('/schedules/', {
        params: { domain_id: activeDomainId },
      })
      return response.data as DigestSchedule[]
    },
  })

  // Fetch history for a schedule
  const { data: history } = useQuery({
    queryKey: ['schedule-history', showHistory],
    queryFn: async () => {
      if (!showHistory) return []
      const response = await api.get(`/schedules/${showHistory}/history`)
      return response.data as ScheduledDigest[]
    },
    enabled: !!showHistory,
  })

  // Create schedule
  const createMutation = useMutation({
    mutationFn: async (data: typeof newSchedule) => {
      return api.post('/schedules/', {
        ...data,
        domain_id: activeDomainId,
        cron_expression: cronPreset === 'custom' ? customCron : cronPreset,
      })
    },
    onSuccess: () => {
      toast.success('Schedule created successfully')
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      setShowAddForm(false)
      resetForm()
    },
    onError: () => {
      toast.error('Failed to create schedule')
    },
  })

  // Toggle schedule
  const toggleMutation = useMutation({
    mutationFn: (id: number) => api.post(`/schedules/${id}/toggle`),
    onSuccess: (response) => {
      const data = response.data
      toast.success(data.message)
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
    },
    onError: () => {
      toast.error('Failed to toggle schedule')
    },
  })

  // Run now
  const runNowMutation = useMutation({
    mutationFn: (id: number) => api.post(`/schedules/${id}/run-now`),
    onSuccess: (response) => {
      const data = response.data
      if (data.digest_id) {
        toast.success(`Digest created: #${data.digest_id}`)
      } else {
        toast.success(data.message)
      }
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['digests'] })
    },
    onError: () => {
      toast.error('Failed to run schedule')
    },
  })

  // Delete schedule
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/schedules/${id}`),
    onSuccess: () => {
      toast.success('Schedule deleted')
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
    },
    onError: () => {
      toast.error('Failed to delete schedule')
    },
  })

  const resetForm = () => {
    setNewSchedule({
      name: '',
      description: '',
      cron_expression: '0 6 * * *',
      timezone: 'UTC',
      lookback_hours: 24,
      max_items: 10,
      top_picks_count: 3,
      cluster_topics: true,
      ai_provider: 'gemini',
    })
    setCronPreset('0 6 * * *')
    setCustomCron('')
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    return new Date(dateStr).toLocaleString()
  }

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '-'
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Calendar className="w-7 h-7" />
            Scheduled Digests
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Automatically generate digests on a schedule
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Schedule
        </button>
      </div>

      {/* Add Form Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-semibold mb-4">Create Schedule</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={newSchedule.name}
                  onChange={(e) =>
                    setNewSchedule({ ...newSchedule, name: e.target.value })
                  }
                  placeholder="Morning Tech Briefing"
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Description (optional)
                </label>
                <textarea
                  value={newSchedule.description}
                  onChange={(e) =>
                    setNewSchedule({
                      ...newSchedule,
                      description: e.target.value,
                    })
                  }
                  placeholder="Daily digest of top tech news"
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Schedule
                </label>
                <select
                  value={cronPreset}
                  onChange={(e) => setCronPreset(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  {CRON_PRESETS.map((preset) => (
                    <option key={preset.value} value={preset.value}>
                      {preset.label}
                    </option>
                  ))}
                </select>
                {cronPreset === 'custom' && (
                  <input
                    type="text"
                    value={customCron}
                    onChange={(e) => setCustomCron(e.target.value)}
                    placeholder="0 6 * * * (minute hour day month day_of_week)"
                    className="w-full mt-2 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 font-mono text-sm"
                  />
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Lookback (hours)
                  </label>
                  <input
                    type="number"
                    value={newSchedule.lookback_hours}
                    onChange={(e) =>
                      setNewSchedule({
                        ...newSchedule,
                        lookback_hours: parseInt(e.target.value) || 24,
                      })
                    }
                    min={1}
                    max={168}
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Max Items
                  </label>
                  <input
                    type="number"
                    value={newSchedule.max_items}
                    onChange={(e) =>
                      setNewSchedule({
                        ...newSchedule,
                        max_items: parseInt(e.target.value) || 10,
                      })
                    }
                    min={1}
                    max={50}
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Top Picks
                  </label>
                  <input
                    type="number"
                    value={newSchedule.top_picks_count}
                    onChange={(e) =>
                      setNewSchedule({
                        ...newSchedule,
                        top_picks_count: parseInt(e.target.value) || 3,
                      })
                    }
                    min={1}
                    max={10}
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    AI Provider
                  </label>
                  <select
                    value={newSchedule.ai_provider}
                    onChange={(e) =>
                      setNewSchedule({
                        ...newSchedule,
                        ai_provider: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  >
                    <option value="gemini">Gemini</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newSchedule.cluster_topics}
                    onChange={(e) =>
                      setNewSchedule({
                        ...newSchedule,
                        cluster_topics: e.target.checked,
                      })
                    }
                    className="rounded"
                  />
                  <span className="text-sm">Cluster by topic</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowAddForm(false)
                  resetForm()
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={() => createMutation.mutate(newSchedule)}
                disabled={!newSchedule.name || createMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
              >
                {createMutation.isPending && (
                  <Loader2 className="w-4 h-4 animate-spin" />
                )}
                Create Schedule
              </button>
            </div>
          </div>
        </div>
      )}

      {/* History Modal */}
      {showHistory && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <History className="w-5 h-5" />
                Schedule History
              </h2>
              <button
                onClick={() => setShowHistory(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                Close
              </button>
            </div>

            {history && history.length > 0 ? (
              <div className="space-y-3">
                {history.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">
                          Digest #{item.digest_id}
                        </div>
                        <div className="text-sm text-gray-500">
                          {formatDate(item.triggered_at)}
                        </div>
                      </div>
                      <div className="text-right text-sm">
                        <div>
                          {item.papers_included} / {item.papers_considered}{' '}
                          papers
                        </div>
                        <div className="text-gray-500">
                          {formatDuration(item.generation_time_seconds)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No history yet. Run the schedule to generate digests.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Schedules List */}
      {schedules && schedules.length > 0 ? (
        <div className="grid gap-4">
          {schedules.map((schedule) => (
            <div
              key={schedule.id}
              className={`p-4 bg-white dark:bg-gray-800 rounded-lg border ${
                schedule.is_active
                  ? 'border-green-200 dark:border-green-800'
                  : 'border-gray-200 dark:border-gray-700'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-lg">{schedule.name}</h3>
                    {schedule.is_active ? (
                      <span className="px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded-full">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full">
                        Paused
                      </span>
                    )}
                  </div>
                  {schedule.description && (
                    <p className="text-gray-500 text-sm mt-1">
                      {schedule.description}
                    </p>
                  )}

                  <div className="flex flex-wrap gap-4 mt-3 text-sm text-gray-600 dark:text-gray-400">
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">
                        {schedule.cron_expression}
                      </code>
                    </div>
                    <div>
                      {schedule.lookback_hours}h lookback
                    </div>
                    <div>
                      Max {schedule.max_items} items
                    </div>
                    <div>
                      Top {schedule.top_picks_count} picks
                    </div>
                  </div>

                  <div className="flex gap-4 mt-2 text-sm">
                    <div>
                      <span className="text-gray-500">Last run:</span>{' '}
                      {formatDate(schedule.last_run_at)}
                    </div>
                    <div>
                      <span className="text-gray-500">Next run:</span>{' '}
                      {formatDate(schedule.next_run_at)}
                    </div>
                    <div>
                      <span className="text-gray-500">Total runs:</span>{' '}
                      {schedule.run_count}
                    </div>
                  </div>

                  {schedule.last_error && (
                    <div className="mt-2 text-sm text-red-600 flex items-center gap-1">
                      <XCircle className="w-4 h-4" />
                      {schedule.last_error}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowHistory(schedule.id)}
                    className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
                    title="View history"
                  >
                    <History className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => runNowMutation.mutate(schedule.id)}
                    disabled={runNowMutation.isPending}
                    className="p-2 text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded-lg"
                    title="Run now"
                  >
                    {runNowMutation.isPending ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Zap className="w-5 h-5" />
                    )}
                  </button>
                  <button
                    onClick={() => toggleMutation.mutate(schedule.id)}
                    className={`p-2 rounded-lg ${
                      schedule.is_active
                        ? 'text-yellow-500 hover:text-yellow-700 hover:bg-yellow-50'
                        : 'text-green-500 hover:text-green-700 hover:bg-green-50'
                    }`}
                    title={schedule.is_active ? 'Pause' : 'Activate'}
                  >
                    {schedule.is_active ? (
                      <Pause className="w-5 h-5" />
                    ) : (
                      <Play className="w-5 h-5" />
                    )}
                  </button>
                  <button
                    onClick={() => {
                      if (
                        confirm(
                          'Are you sure you want to delete this schedule?'
                        )
                      ) {
                        deleteMutation.mutate(schedule.id)
                      }
                    }}
                    className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg"
                    title="Delete"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <Calendar className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            No schedules yet
          </h3>
          <p className="text-gray-500 mt-1">
            Create a schedule to automatically generate digests
          </p>
          <button
            onClick={() => setShowAddForm(true)}
            className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
          >
            Create First Schedule
          </button>
        </div>
      )}
    </div>
  )
}
