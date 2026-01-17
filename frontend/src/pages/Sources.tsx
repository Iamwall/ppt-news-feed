import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { useState } from 'react'
import {
  Rss,
  Plus,
  Trash2,
  ExternalLink,
  Loader2,
  CheckCircle,
  XCircle,
  TestTube,
} from 'lucide-react'
import { sourcesApi } from '../api/client'
import { useBranding } from '../contexts/BrandingContext'

interface Source {
  id: string | number
  name: string
  description: string
  type: string
  url?: string
  requiresApiKey?: boolean
  domains?: string[]
  isCustom: boolean
  isEnabled: boolean
}

interface SourcesResponse {
  domainId: string
  sources: Source[]
}

export default function Sources() {
  const queryClient = useQueryClient()
  const { activeDomainId } = useBranding()
  const [showAddForm, setShowAddForm] = useState(false)
  const [testingUrl, setTestingUrl] = useState<string | null>(null)
  const [newSource, setNewSource] = useState({
    name: '',
    url: '',
    description: '',
  })

  const { data: sourcesData, isLoading } = useQuery({
    queryKey: ['sources', activeDomainId],
    queryFn: async () => {
      const response = await sourcesApi.list()
      return response.data as SourcesResponse
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: { name: string; url: string; description?: string }) =>
      sourcesApi.create(data),
    onSuccess: () => {
      toast.success('Source added successfully')
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      setShowAddForm(false)
      setNewSource({ name: '', url: '', description: '' })
    },
    onError: () => {
      toast.error('Failed to add source')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => sourcesApi.delete(id),
    onSuccess: () => {
      toast.success('Source deleted')
      queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
    onError: () => {
      toast.error('Failed to delete source')
    },
  })

  const testMutation = useMutation({
    mutationFn: (url: string) => sourcesApi.test(url),
    onSuccess: (response) => {
      const data = response.data
      if (data.valid) {
        toast.success(`Valid feed: ${data.title} (${data.entryCount} entries)`)
      } else {
        toast.error(`Invalid feed: ${data.error}`)
      }
      setTestingUrl(null)
    },
    onError: () => {
      toast.error('Failed to test feed')
      setTestingUrl(null)
    },
  })

  const handleTestUrl = (url: string) => {
    setTestingUrl(url)
    testMutation.mutate(url)
  }

  const handleAddSource = () => {
    if (!newSource.name || !newSource.url) {
      toast.error('Name and URL are required')
      return
    }
    createMutation.mutate(newSource)
  }

  const builtinSources = sourcesData?.sources.filter((s) => !s.isCustom) || []
  const customSources = sourcesData?.sources.filter((s) => s.isCustom) || []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-science-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-semibold text-ink-50">
            Content Sources
          </h1>
          <p className="text-ink-400 mt-1">
            Manage built-in and custom RSS feed sources for your domain
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowAddForm(true)}
          className="btn-primary"
        >
          <Plus className="w-4 h-4" />
          Add Custom Source
        </button>
      </div>

      {/* Add Source Form */}
      {showAddForm && (
        <div className="card p-6">
          <h2 className="font-medium text-ink-100 mb-4 flex items-center gap-2">
            <Rss className="w-5 h-5 text-science-400" />
            Add Custom RSS Feed
          </h2>
          <div className="space-y-4">
            <div>
              <label className="label">Source Name</label>
              <input
                type="text"
                value={newSource.name}
                onChange={(e) =>
                  setNewSource((s) => ({ ...s, name: e.target.value }))
                }
                placeholder="e.g., My Tech Blog"
                className="input"
              />
            </div>
            <div>
              <label className="label">RSS Feed URL</label>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={newSource.url}
                  onChange={(e) =>
                    setNewSource((s) => ({ ...s, url: e.target.value }))
                  }
                  placeholder="https://example.com/feed.xml"
                  className="input flex-1"
                />
                <button
                  type="button"
                  onClick={() => newSource.url && handleTestUrl(newSource.url)}
                  disabled={!newSource.url || testingUrl === newSource.url}
                  className="btn-secondary"
                >
                  {testingUrl === newSource.url ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <TestTube className="w-4 h-4" />
                  )}
                  Test
                </button>
              </div>
            </div>
            <div>
              <label className="label">Description (optional)</label>
              <input
                type="text"
                value={newSource.description}
                onChange={(e) =>
                  setNewSource((s) => ({ ...s, description: e.target.value }))
                }
                placeholder="Brief description of this source"
                className="input"
              />
            </div>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false)
                  setNewSource({ name: '', url: '', description: '' })
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleAddSource}
                disabled={createMutation.isPending}
                className="btn-primary"
              >
                {createMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
                Add Source
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Built-in Sources */}
      <div className="card p-6">
        <h2 className="font-medium text-ink-100 mb-4 flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-500" />
          Built-in Sources ({builtinSources.length})
        </h2>
        <p className="text-sm text-ink-400 mb-4">
          These sources are pre-configured for the current domain and are available for fetching.
        </p>
        <div className="grid gap-3">
          {builtinSources.map((source) => (
            <div
              key={source.id}
              className="flex items-center justify-between p-3 bg-ink-800/50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-ink-700 flex items-center justify-center">
                  <Rss className="w-4 h-4 text-ink-400" />
                </div>
                <div>
                  <h3 className="font-medium text-ink-100">{source.name}</h3>
                  <p className="text-xs text-ink-400">{source.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs px-2 py-1 bg-ink-700 rounded text-ink-300">
                  {source.type}
                </span>
                {source.isEnabled ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <XCircle className="w-4 h-4 text-ink-500" />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Custom Sources */}
      <div className="card p-6">
        <h2 className="font-medium text-ink-100 mb-4 flex items-center gap-2">
          <Rss className="w-5 h-5 text-science-400" />
          Custom Sources ({customSources.length})
        </h2>
        {customSources.length === 0 ? (
          <div className="text-center py-8 text-ink-400">
            <Rss className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No custom sources yet.</p>
            <p className="text-sm">Add RSS feeds to aggregate content from your favorite sources.</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {customSources.map((source) => (
              <div
                key={source.id}
                className="flex items-center justify-between p-3 bg-ink-800/50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-science-600/20 flex items-center justify-center">
                    <Rss className="w-4 h-4 text-science-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-ink-100">{source.name}</h3>
                    <p className="text-xs text-ink-400">
                      {source.description || source.url}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {source.url && (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 text-ink-400 hover:text-ink-200"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                  <button
                    type="button"
                    onClick={() => deleteMutation.mutate(source.id as number)}
                    disabled={deleteMutation.isPending}
                    className="p-2 text-red-400 hover:text-red-300"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
