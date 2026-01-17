import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { 
  ArrowLeft,
  Save,
  Eye,
  Download,
  Send,
  Loader2,
  FileText,
  Mail,
  X
} from 'lucide-react'
import { digestsApi, newsletterApi, api } from '../api/client'
import { Digest } from '../types'

export default function NewsletterEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [name, setName] = useState('')
  const [introText, setIntroText] = useState('')
  const [conclusionText, setConclusionText] = useState('')
  const [showSendModal, setShowSendModal] = useState(false)
  const [recipients, setRecipients] = useState('')
  
  const { data: digest, isLoading } = useQuery<Digest>({
    queryKey: ['digest', id],
    queryFn: () => digestsApi.get(Number(id)).then(res => res.data),
    enabled: !!id,
  })

  // Integrated Preview query
  const previewQuery = useQuery({
    queryKey: ['newsletter-preview', id],
    queryFn: () => newsletterApi.preview(Number(id)).then(res => res.data),
    enabled: !!id,
  })
  
  // Initialize form with digest data
  useEffect(() => {
    if (digest) {
      setName(digest.name || '')
      setIntroText(digest.intro_text || '')
      setConclusionText(digest.conclusion_text || '')
    }
  }, [digest])
  
  const updateMutation = useMutation({
    mutationFn: (updates: Record<string, string>) => 
      api.put(`digests/${id}`, updates),
    onSuccess: () => {
      toast.success('Newsletter saved')
      queryClient.invalidateQueries({ queryKey: ['digest', id] })
      queryClient.invalidateQueries({ queryKey: ['newsletter-preview', id] })
      queryClient.invalidateQueries({ queryKey: ['digests'] })
    },
    onError: () => {
      toast.error('Failed to save')
    },
  })
  
  const exportMutation = useMutation({
    mutationFn: (format: 'html' | 'pdf' | 'markdown') => 
      newsletterApi.export(Number(id), format),
    onSuccess: (response, format) => {
      const blob = response.data as Blob
      
      // Basic check if the blob is actually an error message
      if (blob.size < 500 && blob.type.includes('application/json')) {
        toast.error('Export failed: Server returned an error')
        return
      }

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      const extension = format === 'markdown' ? 'md' : format
      a.download = `newsletter_${id}_${new Date().toISOString().split('T')[0]}.${extension}`
      document.body.appendChild(a)
      a.click()
      
      // Cleanup
      setTimeout(() => {
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }, 100)
      
      toast.success(`Exported as ${format.toUpperCase()}`)
    },
    onError: (error: any) => {
      console.error('Export Error:', error)
      toast.error('Export failed: Network error or server failure')
    },

  })
  
  const sendMutation = useMutation({
    mutationFn: (recipientList: string[]) => 
      newsletterApi.send(Number(id), recipientList),
    onSuccess: (response) => {
      toast.success(`Sent to ${response.data.sent} recipients`)
      setShowSendModal(false)
      setRecipients('')

    },
    onError: () => {
      toast.error('Failed to send')
    },
  })
  
  const handleSave = () => {
    updateMutation.mutate({
      name,
      intro_text: introText,
      conclusion_text: conclusionText,
    })
  }
  
  const handleSend = () => {
    const recipientList = recipients
      .split(/[,\n]/)
      .map(e => e.trim())
      .filter(e => e.includes('@'))
    
    if (recipientList.length === 0) {
      toast.error('Enter at least one valid email')
      return
    }
    
    sendMutation.mutate(recipientList)
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-science-500 animate-spin" />
      </div>
    )
  }
  
  if (!digest) {
    return (
      <div className="text-center py-20">
        <p className="text-ink-400">Digest not found</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/newsletters')}
            className="p-2 hover:bg-ink-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-ink-400" />
          </button>
          <div>
            <h1 className="font-display text-2xl font-semibold text-ink-50">
              Edit Newsletter
            </h1>
            <p className="text-ink-400 text-sm">
              {digest.digest_papers?.length || 0} papers
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['newsletter-preview', id] })}
            disabled={previewQuery.isFetching}
            className="btn-secondary"
          >
            {previewQuery.isFetching ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Eye className="w-4 h-4" />
            )}
            Refresh Preview
          </button>
          <button
            onClick={handleSave}
            disabled={updateMutation.isPending}
            className="btn-secondary"
          >
            {updateMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Save
          </button>
          <button
            onClick={() => setShowSendModal(true)}
            className="btn-primary"
          >
            <Send className="w-4 h-4" />
            Publish
          </button>
        </div>
      </div>
      
      {/* Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* Left: Editor */}
        <div className="space-y-6">
          <div className="card p-6">
            <label className="label">Newsletter Title</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="Weekly Research Digest"
            />
          </div>
          
          <div className="card p-6">
            <label className="label">Introduction</label>
            <textarea
              value={introText}
              onChange={(e) => setIntroText(e.target.value)}
              className="input min-h-[150px] resize-y"
              placeholder="Welcome to this week's digest..."
            />
          </div>
          
          <div className="card p-6">
            <label className="label">Conclusion</label>
            <textarea
              value={conclusionText}
              onChange={(e) => setConclusionText(e.target.value)}
              className="input min-h-[100px] resize-y"
              placeholder="That's all for this week..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card p-6">
              <h3 className="font-medium text-ink-100 mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-science-400" />
                Included Papers
              </h3>
              <div className="space-y-3 max-h-[300px] overflow-y-auto">
                {digest.digest_papers?.map((dp, i) => (
                  <div 
                    key={dp.paper?.id || i}
                    className="p-3 bg-ink-800/50 rounded-lg border border-ink-700"
                  >
                    <p className="text-sm text-ink-200 font-medium line-clamp-2">
                      {dp.paper?.title}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="card p-6">
              <h3 className="font-medium text-ink-100 mb-4 flex items-center gap-2">
                <Download className="w-5 h-5 text-science-400" />
                Export
              </h3>
              <div className="space-y-3">
                <button
                  onClick={() => exportMutation.mutate('html')}
                  disabled={exportMutation.isPending}
                  className="btn-secondary w-full justify-center"
                >
                  HTML
                </button>
                <button
                  onClick={() => exportMutation.mutate('pdf')}
                  disabled={exportMutation.isPending}
                  className="btn-secondary w-full justify-center"
                >
                  PDF
                </button>
                <button
                  onClick={() => exportMutation.mutate('markdown')}
                  disabled={exportMutation.isPending}
                  className="btn-secondary w-full justify-center"
                >
                  Markdown
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {/* Right: Live Preview */}
        <div className="sticky top-8">
          <div className="card h-[calc(100vh-120px)] flex flex-col bg-white overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b bg-gray-50">
              <h3 className="font-medium text-gray-900 flex items-center gap-2">
                <Eye className="w-5 h-5 text-gray-400" />
                Integrated Preview
              </h3>
              {previewQuery.isFetching && (
                <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
              )}
            </div>
            
            <div className="flex-1 overflow-auto bg-gray-100 p-8">
              {previewQuery.isLoading ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <Loader2 className="w-12 h-12 animate-spin mb-4" />
                  <p>Loading preview...</p>
                </div>
              ) : previewQuery.isError ? (
                <div className="flex flex-col items-center justify-center h-full text-red-500 p-8 text-center">
                  <X className="w-12 h-12 mb-4" />
                  <p className="font-medium">Failed to load preview</p>
                  <p className="text-sm mt-2">Check backend status and try refreshing.</p>
                </div>
              ) : (
                <div 
                  className="bg-white shadow-lg mx-auto max-w-[800px] min-h-full"
                  dangerouslySetInnerHTML={{ __html: previewQuery.data || '' }}
                />
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Send Modal */}
      {showSendModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-8">
          <div className="card max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-ink-100 flex items-center gap-2">
                <Mail className="w-5 h-5 text-science-400" />
                Send Newsletter
              </h3>
              <button
                onClick={() => setShowSendModal(false)}
                className="p-2 hover:bg-ink-700 rounded-lg"
              >
                <X className="w-5 h-5 text-ink-400" />
              </button>
            </div>
            
            <label className="label">Recipients</label>
            <textarea
              value={recipients}
              onChange={(e) => setRecipients(e.target.value)}
              className="input min-h-[120px] resize-none"
              placeholder="email@example.com&#10;another@example.com"
            />
            <p className="text-xs text-ink-500 mt-2 mb-4">
              One email per line, or comma-separated
            </p>
            
            <div className="flex gap-3">
              <button
                onClick={() => setShowSendModal(false)}
                className="btn-secondary flex-1 justify-center"
              >
                Cancel
              </button>
              <button
                onClick={handleSend}
                disabled={sendMutation.isPending}
                className="btn-primary flex-1 justify-center"
              >
                {sendMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
