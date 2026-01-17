import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { useState, useEffect } from 'react'
import { 
  Cpu,
  Image,
  Shield,
  Save,
  Loader2
} from 'lucide-react'
import { settingsApi } from '../api/client'

export default function Settings() {
  const queryClient = useQueryClient()
  
  const { data: settingsData, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.get(),
  })
  
  const { data: weightsData } = useQuery({
    queryKey: ['credibility-weights'],
    queryFn: () => settingsApi.getCredibilityWeights(),
  })
  
  const [settings, setSettings] = useState({
    default_ai_provider: 'openai',
    default_ai_model: 'gpt-4o',
    default_summary_style: 'newsletter',
    default_image_provider: 'gemini',
    generate_images_by_default: true,
    default_max_results: 50,
    default_days_back: 7,
  })
  
  const [weights, setWeights] = useState({
    journal_impact_weight: 0.25,
    author_hindex_weight: 0.15,
    sample_size_weight: 0.20,
    methodology_weight: 0.20,
    peer_review_weight: 0.10,
    citation_velocity_weight: 0.10,
  })
  
  useEffect(() => {
    if (settingsData?.data) {
      setSettings(prev => ({ ...prev, ...settingsData.data }))
    }
  }, [settingsData])
  
  useEffect(() => {
    if (weightsData?.data) {
      setWeights(weightsData.data)
    }
  }, [weightsData])
  
  const updateSettingsMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => settingsApi.update(data),
    onSuccess: () => {
      toast.success('Settings saved')
      queryClient.invalidateQueries({ queryKey: ['settings'] })
    },
    onError: () => {
      toast.error('Failed to save settings')
    },
  })
  
  const updateWeightsMutation = useMutation({
    mutationFn: (data: Record<string, number>) => 
      settingsApi.updateCredibilityWeights(data),
    onSuccess: () => {
      toast.success('Weights saved')
      queryClient.invalidateQueries({ queryKey: ['credibility-weights'] })
    },
    onError: () => {
      toast.error('Failed to save weights')
    },
  })
  
  const handleSaveSettings = () => {
    updateSettingsMutation.mutate(settings)
  }
  
  const handleSaveWeights = () => {
    updateWeightsMutation.mutate(weights)
  }
  
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
      <div>
        <h1 className="font-display text-3xl font-semibold text-ink-50">
          Settings
        </h1>
        <p className="text-ink-400 mt-1">
          Configure AI providers, defaults, and credibility scoring
        </p>
      </div>
      
      {/* AI Settings */}
      <div className="card p-6">
        <h2 className="font-medium text-ink-100 mb-6 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-science-400" />
          AI Configuration
        </h2>
        
        <div className="grid sm:grid-cols-2 gap-6">
          <div>
            <label className="label">Default AI Provider</label>
            <select
              value={settings.default_ai_provider}
              onChange={(e) => setSettings(s => ({ ...s, default_ai_provider: e.target.value }))}
              className="input"
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic Claude</option>
              <option value="ollama">Ollama (Local)</option>
            </select>
          </div>
          
          <div>
            <label className="label">Default Model</label>
            <select
              value={settings.default_ai_model}
              onChange={(e) => setSettings(s => ({ ...s, default_ai_model: e.target.value }))}
              className="input"
            >
              <optgroup label="OpenAI">
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
              </optgroup>
              <optgroup label="Anthropic">
                <option value="claude-sonnet-4-20250514">Claude Sonnet 4</option>
                <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
              </optgroup>
              <optgroup label="Ollama">
                <option value="llama3">Llama 3</option>
                <option value="mistral">Mistral</option>
              </optgroup>
            </select>
          </div>
          
          <div>
            <label className="label">Summary Style</label>
            <select
              value={settings.default_summary_style}
              onChange={(e) => setSettings(s => ({ ...s, default_summary_style: e.target.value }))}
              className="input"
            >
              <option value="newsletter">Newsletter (Engaging)</option>
              <option value="technical">Technical (Detailed)</option>
              <option value="layperson">Layperson (Simple)</option>
            </select>
          </div>
          
          <div>
            <label className="label">Default Max Results</label>
            <input
              type="number"
              value={settings.default_max_results}
              onChange={(e) => setSettings(s => ({ ...s, default_max_results: Number(e.target.value) }))}
              min={10}
              max={500}
              className="input"
            />
          </div>
        </div>
        
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleSaveSettings}
            disabled={updateSettingsMutation.isPending}
            className="btn-primary"
          >
            {updateSettingsMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Save Settings
          </button>
        </div>
      </div>
      
      {/* Image Settings */}
      <div className="card p-6">
        <h2 className="font-medium text-ink-100 mb-6 flex items-center gap-2">
          <Image className="w-5 h-5 text-science-400" />
          Image Generation
        </h2>
        
        <div className="grid sm:grid-cols-2 gap-6">
          <div>
            <label className="label">Image Provider</label>
            <select
              value={settings.default_image_provider}
              onChange={(e) => setSettings(s => ({ ...s, default_image_provider: e.target.value }))}
              className="input"
            >
              <option value="gemini">Google Gemini (Imagen)</option>
              <option value="dalle">OpenAI DALL-E 3</option>
            </select>
          </div>
          
          <div className="flex items-center">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.generate_images_by_default}
                onChange={(e) => setSettings(s => ({ ...s, generate_images_by_default: e.target.checked }))}
                className="w-5 h-5 rounded border-ink-600 bg-ink-800 text-science-500 focus:ring-science-500"
              />
              <span className="text-ink-200">Generate images by default</span>
            </label>
          </div>
        </div>
      </div>
      
      {/* Credibility Weights */}
      <div className="card p-6">
        <h2 className="font-medium text-ink-100 mb-2 flex items-center gap-2">
          <Shield className="w-5 h-5 text-science-400" />
          Credibility Scoring Weights
        </h2>
        <p className="text-sm text-ink-400 mb-6">
          Adjust how different factors contribute to the credibility score. 
          Weights will be normalized to sum to 100%.
        </p>
        
        <div className="space-y-4">
          {[
            { key: 'journal_impact_weight', label: 'Journal Impact Factor', desc: 'Higher for well-known journals' },
            { key: 'author_hindex_weight', label: 'Author H-Index', desc: 'Publication history of authors' },
            { key: 'sample_size_weight', label: 'Sample Size', desc: 'Study participant/data point count' },
            { key: 'methodology_weight', label: 'Methodology Quality', desc: 'Study design (RCT, meta-analysis, etc.)' },
            { key: 'peer_review_weight', label: 'Peer Review Status', desc: 'Published vs. preprint' },
            { key: 'citation_velocity_weight', label: 'Citation Velocity', desc: 'How quickly paper is being cited' },
          ].map(({ key, label, desc }) => (
            <div key={key} className="flex items-center gap-4">
              <div className="flex-1">
                <label className="text-sm font-medium text-ink-200">
                  {label}
                </label>
                <p className="text-xs text-ink-500">{desc}</p>
              </div>
              <div className="w-32">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={weights[key as keyof typeof weights]}
                  onChange={(e) => setWeights(w => ({ 
                    ...w, 
                    [key]: parseFloat(e.target.value) 
                  }))}
                  className="w-full accent-science-500"
                />
              </div>
              <div className="w-16 text-right">
                <span className="text-sm font-mono text-ink-300">
                  {Math.round(weights[key as keyof typeof weights] * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleSaveWeights}
            disabled={updateWeightsMutation.isPending}
            className="btn-primary"
          >
            {updateWeightsMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Save Weights
          </button>
        </div>
      </div>
    </div>
  )
}
