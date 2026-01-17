import { useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { 
  Download,
  Mail,
  RefreshCw,
  Loader2,
  FileText,
  FileImage,
  ExternalLink
} from 'lucide-react'
import { format } from 'date-fns'
import { digestsApi, newsletterApi, getImageUrl } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import CredibilityBadge from '../components/CredibilityBadge'
import { useState } from 'react'
import { Digest } from '../types'

export default function DigestDetail() {
  const { id } = useParams<{ id: string }>()
  const digestId = Number(id)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [recipients, setRecipients] = useState('')
  const [lightboxImage, setLightboxImage] = useState<string | null>(null)
  
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['digest', digestId],
    queryFn: () => digestsApi.get(digestId),
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status
      return status === 'processing' || status === 'pending' ? 3000 : false
    },
  })
  
  const regenerateMutation = useMutation({
    mutationFn: () => digestsApi.regenerate(digestId),
    onSuccess: () => {
      toast.success('Regenerating digest...')
      refetch()
    },
    onError: () => {
      toast.error('Failed to regenerate')
    },
  })
  
  const exportMutation = useMutation({
    mutationFn: (format: 'html' | 'pdf' | 'markdown') => 
      newsletterApi.export(digestId, format),
    onSuccess: (response, format) => {
      // Create download
      const blob = format === 'pdf' 
        ? response.data 
        : new Blob([response.data], { type: format === 'html' ? 'text/html' : 'text/markdown' })
      
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `newsletter_${digestId}.${format === 'markdown' ? 'md' : format}`
      a.click()
      URL.revokeObjectURL(url)
      
      toast.success('Downloaded!')
    },
    onError: () => {
      toast.error('Export failed')
    },
  })
  
  const sendEmailMutation = useMutation({
    mutationFn: (emails: string[]) => newsletterApi.send(digestId, emails),
    onSuccess: (response) => {
      toast.success(`Sent to ${response.data.sent} recipients`)
      setShowEmailModal(false)
      setRecipients('')
    },
    onError: () => {
      toast.error('Failed to send emails')
    },
  })
  
  const digest = data?.data as Digest | undefined
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-science-500 animate-spin" />
      </div>
    )
  }
  
  if (!digest) {
    return (
      <div className="card p-12 text-center">
        <h3 className="text-lg font-medium text-ink-300">
          Digest not found
        </h3>
      </div>
    )
  }
  
  const papers = digest.digest_papers?.map(dp => dp.paper) || []
  
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="font-display text-3xl font-semibold text-ink-50">
              {digest.name}
            </h1>
            <StatusBadge status={digest.status} />
          </div>
          <p className="text-ink-400">
            Created {format(new Date(digest.created_at), 'MMMM d, yyyy')} • 
            {papers.length} papers
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => regenerateMutation.mutate()}
            disabled={regenerateMutation.isPending || digest.status === 'processing'}
            className="btn-secondary"
          >
            <RefreshCw className={`w-4 h-4 ${regenerateMutation.isPending ? 'animate-spin' : ''}`} />
            Regenerate
          </button>
          
          {digest.status === 'completed' && (
            <>
              <div className="relative group">
                <button className="btn-secondary">
                  <Download className="w-4 h-4" />
                  Export
                </button>
                
                <div className="absolute right-0 top-full mt-2 w-48 card p-2 hidden group-hover:block z-10">
                  <button
                    onClick={() => exportMutation.mutate('html')}
                    className="w-full px-3 py-2 text-left text-sm text-ink-200 hover:bg-ink-800 rounded flex items-center gap-2"
                  >
                    <FileText className="w-4 h-4" />
                    HTML
                  </button>
                  <button
                    onClick={() => exportMutation.mutate('pdf')}
                    className="w-full px-3 py-2 text-left text-sm text-ink-200 hover:bg-ink-800 rounded flex items-center gap-2"
                  >
                    <FileImage className="w-4 h-4" />
                    PDF
                  </button>
                  <button
                    onClick={() => exportMutation.mutate('markdown')}
                    className="w-full px-3 py-2 text-left text-sm text-ink-200 hover:bg-ink-800 rounded flex items-center gap-2"
                  >
                    <FileText className="w-4 h-4" />
                    Markdown
                  </button>
                </div>
              </div>
              
              <button
                onClick={() => setShowEmailModal(true)}
                className="btn-primary"
              >
                <Mail className="w-4 h-4" />
                Send Email
              </button>
            </>
          )}
        </div>
      </div>
      
      {/* Processing indicator */}
      {(digest.status === 'processing' || digest.status === 'pending') && (
        <div className="card p-6 border-science-600/30 bg-science-950/20">
          <div className="flex items-center gap-4">
            <Loader2 className="w-8 h-8 text-science-400 animate-spin" />
            <div>
              <h3 className="font-medium text-ink-100">
                Processing digest...
              </h3>
              <p className="text-sm text-ink-400">
                AI is generating summaries, credibility analysis, and images
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Error */}
      {digest.status === 'failed' && digest.error_message && (
        <div className="card p-6 border-accent-600/30 bg-accent-950/20">
          <h3 className="font-medium text-accent-400 mb-2">Processing Failed</h3>
          <p className="text-ink-300 text-sm">{digest.error_message}</p>
        </div>
      )}
      
      {/* Intro */}
      {digest.intro_text && (
        <div className="card p-6 border-l-4 border-science-500 bg-science-950/20">
          <h3 className="text-sm font-semibold text-science-400 uppercase tracking-wider mb-2">Introduction</h3>
          <p className="text-ink-50 text-lg leading-relaxed font-serif">
            {digest.intro_text}
          </p>
        </div>
      )}

      {/* Connecting Narrative - NEW */}
      {digest.connecting_narrative && (
        <div className="card p-8 bg-gradient-to-br from-ink-900 to-ink-950 border-ink-800 shadow-xl">
           <div className="flex items-center gap-3 mb-4">
             <div className="h-px bg-science-500/50 flex-1"></div>
             <h2 className="font-display text-2xl font-semibold text-ink-50 text-center">The Connected Store</h2>
             <div className="h-px bg-science-500/50 flex-1"></div>
           </div>
           <div className="prose prose-invert prose-lg max-w-none text-ink-200 leading-relaxed font-serif">
             <div dangerouslySetInnerHTML={{ __html: digest.connecting_narrative.replace(/\n/g, '<br />') }} />
           </div>
        </div>
      )}
      
      {/* Papers */}
      <div className="space-y-8 mt-12">
        <h3 className="font-display text-2xl font-semibold text-ink-50">Featured Research</h3>
        
        {papers.map((paper, index) => (
          <article key={paper.id} className="card overflow-hidden transition-all duration-300 hover:shadow-2xl hover:border-science-600/30">
            <div className="flex flex-col md:flex-row-reverse">
              {/* Image - only if available */}
              {paper.image_path && (
                <div className="md:flex-shrink-0 relative self-stretch flex items-center">
                  <img
                    src={getImageUrl(paper.image_path) || ''}
                    alt={paper.title}
                    onClick={() => setLightboxImage(getImageUrl(paper.image_path) || '')}
                    className="h-auto max-h-full w-auto max-w-[500px] object-contain bg-ink-900 rounded-r-lg cursor-zoom-in hover:opacity-90 transition-opacity"
                  />
                </div>
              )}
              
              <div className={`p-8 flex flex-col flex-grow ${paper.image_path ? 'md:w-1/2' : 'w-full'}`}>
                {/* Header */}
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-base font-bold text-science-400 bg-science-950/50 px-2 py-0.5 rounded border border-science-900">
                         FINDING #{index + 1}
                      </span>
                      <span className="text-base text-ink-400">{paper.journal || 'Unknown journal'}</span>
                    </div>
                    
                    <h3 className="font-display text-2xl font-bold text-ink-50 leading-snug mb-2">
                      {paper.summary_headline || paper.title}
                    </h3>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <CredibilityBadge score={paper.credibility_score} />
                    
                    {paper.url && (
                      <a
                        href={paper.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-ink-400 hover:text-science-400 p-2 hover:bg-ink-800 rounded-full transition-colors"
                        title="View Original Paper"
                      >
                        <ExternalLink className="w-5 h-5" />
                      </a>
                    )}
                  </div>
                </div>
                
                <div className="space-y-6 flex-grow">
                   {/* Main Takeaway */}
                   {paper.summary_takeaway && (
                     <div className="bg-ink-900/50 p-4 rounded-lg border-l-2 border-science-500">
                       <p className="text-ink-100 italic text-xl leading-relaxed">
                         "{paper.summary_takeaway}"
                       </p>
                     </div>
                   )}

                   {/* Key Takeaways - The actionable parts */}
                   {paper.key_takeaways && paper.key_takeaways.length > 0 && (
                     <div className="grid gap-3">
                       <h4 className="text-base font-semibold text-ink-400 uppercase tracking-wider">Actionable Insights</h4>
                       {paper.key_takeaways.map((takeaway, i) => {
                         // Alternate colors for standard library feeling
                         const colors = [
                           "border-accent-500 bg-accent-950/20 text-accent-100",
                           "border-success-500 bg-success-950/20 text-success-100", 
                           "border-science-500 bg-science-950/20 text-science-100"
                         ];
                         const colorClass = colors[i % colors.length];
                         
                         // Parse markdown bold if present
                         const parts = typeof takeaway === 'string' ? takeaway.split('**:') : [takeaway];
                         const label = parts.length > 1 ? parts[0].replace('**', '') : null;
                         const text = parts.length > 1 ? parts[1] : parts[0];
                         
                         return (
                           <div key={i} className={`p-4 rounded border-l-4 ${colorClass}`}>
                             <p className="text-base leading-relaxed">
                               {label && <span className="font-bold block mb-1 uppercase text-sm opacity-80">{label}</span>}
                               {text}
                             </p>
                           </div>
                         );
                       })}
                     </div>
                   )}
                   
                   {/* Why it matters */}
                   {paper.summary_why_matters && (
                      <p className="text-ink-300 text-base leading-relaxed">
                        <span className="font-semibold text-science-400">Why it matters:</span> {paper.summary_why_matters}
                      </p>
                   )}
                </div>
                
                {/* Footer details */}
                <div className="mt-6 pt-4 border-t border-ink-800 flex flex-wrap items-center justify-between gap-4">
                  {/* Tags */}
                  {paper.tags && paper.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {paper.tags.map((tag, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-full bg-ink-800 text-xs text-ink-300 border border-ink-700">
                          #{tag.replace(/\s+/g, '')}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Credibility note */}
                  {paper.credibility_note && (
                    <div className="text-xs text-ink-500">
                      <span className="font-medium text-ink-400">Analysis:</span> {paper.credibility_note}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
      
      {/* Conclusion / Final Thoughts */}
      {digest.conclusion_text && (
        <div className="card p-8 bg-science-950/30 border-science-800 mt-12">
          <h3 className="text-xl font-display font-semibold text-science-200 mb-6 text-center">Final Thoughts</h3>

          {/* Summary Infographic */}
          {digest.summary_image_path && (
            <div className="flex justify-center mb-8">
              <img
                src={getImageUrl(digest.summary_image_path) || ''}
                alt="Newsletter Summary Infographic"
                onClick={() => setLightboxImage(getImageUrl(digest.summary_image_path) || '')}
                className="max-w-2xl w-full h-auto rounded-lg shadow-xl cursor-zoom-in hover:opacity-90 transition-opacity border border-ink-700"
              />
            </div>
          )}

          <div className="text-ink-100 leading-relaxed max-w-3xl mx-auto space-y-4">
            {digest.conclusion_text.split('\n').map((line, i) => {
              const trimmedLine = line.trim();

              // Handle bullet points with emojis (• or - or *)
              if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ') || trimmedLine.startsWith('• ')) {
                return (
                  <li key={i} className="ml-6 list-none text-ink-200 flex items-start gap-2">
                    <span className="text-science-400">•</span>
                    <span>{trimmedLine.slice(2)}</span>
                  </li>
                );
              }

              // Handle bold headers with emojis (**🎯 text** or **text**)
              if (trimmedLine.startsWith('**') && trimmedLine.includes('**')) {
                const headerMatch = trimmedLine.match(/^\*\*(.+?)\*\*/);
                if (headerMatch) {
                  const headerText = headerMatch[1];
                  const restText = trimmedLine.slice(headerMatch[0].length);

                  // Check for action plan headers (with emojis)
                  const isActionHeader = headerText.includes('🎯') ||
                                        headerText.includes('⚡') ||
                                        headerText.includes('🔬') ||
                                        headerText.includes('💬');

                  return (
                    <div key={i} className={isActionHeader ? 'mt-6' : ''}>
                      <h4 className={`font-semibold text-lg mt-4 mb-2 ${
                        isActionHeader ? 'text-accent-300 text-xl' : 'text-science-300'
                      }`}>
                        {headerText}
                      </h4>
                      {restText && <p className="text-ink-200">{restText}</p>}
                    </div>
                  );
                }
              }

              // Regular paragraph (skip empty lines)
              if (trimmedLine.length > 0) {
                return <p key={i} className="text-ink-200">{trimmedLine}</p>;
              }

              return null;
            })}
          </div>
        </div>
      )}

      {/* Footer Disclaimer */}
      <footer className="mt-16 pt-8 border-t border-ink-800">
        <div className="text-center text-ink-500 text-sm space-y-2">
          <p>
            <strong className="text-ink-400">Disclaimer:</strong> Images in this newsletter are AI-generated 
            illustrations created to complement the research summaries and may not represent actual study visuals.
          </p>
          <p>
            Summaries are AI-generated from published research papers. 
            For complete methodology and findings, please refer to the original publications.
          </p>
        </div>
      </footer>
      
      {/* Email Modal */}
      {showEmailModal && (
        <div className="fixed inset-0 bg-ink-950/80 flex items-center justify-center z-50">
          <div className="card p-6 w-full max-w-md animate-fade-in">
            <h2 className="font-display text-xl font-medium text-ink-50 mb-4">
              Send Newsletter
            </h2>
            
            <div className="mb-6">
              <label className="label">Recipients</label>
              <textarea
                value={recipients}
                onChange={(e) => setRecipients(e.target.value)}
                placeholder="email1@example.com, email2@example.com"
                className="input min-h-[100px] resize-none"
              />
              <p className="text-xs text-ink-500 mt-1">
                Comma-separated email addresses
              </p>
            </div>
            
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowEmailModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const emails = recipients.split(',').map(e => e.trim()).filter(e => e)
                  if (emails.length === 0) {
                    toast.error('Enter at least one email')
                    return
                  }
                  sendEmailMutation.mutate(emails)
                }}
                disabled={sendEmailMutation.isPending}
                className="btn-primary"
              >
                {sendEmailMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Mail className="w-4 h-4" />
                    Send
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Lightbox Modal */}
      {lightboxImage && (
        <div 
          className="fixed inset-0 bg-ink-950/95 flex items-center justify-center z-50 cursor-zoom-out animate-fade-in"
          onClick={() => setLightboxImage(null)}
        >
          <img
            src={lightboxImage}
            alt="Full size preview"
            className="max-w-[90vw] max-h-[90vh] object-contain rounded-lg shadow-2xl"
          />
          <button
            onClick={() => setLightboxImage(null)}
            className="absolute top-6 right-6 text-ink-300 hover:text-ink-50 text-4xl font-light transition-colors"
          >
            ×
          </button>
        </div>
      )}
    </div>
  )
}
