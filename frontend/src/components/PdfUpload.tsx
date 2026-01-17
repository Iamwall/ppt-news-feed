import { useState, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { Upload, FileText, Loader2, CheckCircle, X } from 'lucide-react'
import { api } from '../api/client'

interface UploadResult {
  message: string
  paper: {
    id: number
    title: string
    abstract: string | null
    authors: string[]
    source: string
  }
}

export default function PdfUpload() {
  const queryClient = useQueryClient()
  const [isDragging, setIsDragging] = useState(false)
  const [uploadedPaper, setUploadedPaper] = useState<UploadResult['paper'] | null>(null)

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post<UploadResult>('/papers/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data
    },
    onSuccess: (data) => {
      setUploadedPaper(data.paper)
      toast.success(`Uploaded: ${data.paper.title.slice(0, 50)}...`)
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || 'Failed to upload PDF'
      toast.error(message)
    },
  })

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const file = e.dataTransfer.files[0]
    if (file && file.type === 'application/pdf') {
      uploadMutation.mutate(file)
    } else {
      toast.error('Please drop a PDF file')
    }
  }, [uploadMutation])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadMutation.mutate(file)
    }
  }

  const clearUpload = () => {
    setUploadedPaper(null)
  }

  return (
    <div className="card p-6">
      <h2 className="font-medium text-ink-100 mb-4 flex items-center gap-2">
        <Upload className="w-5 h-5 text-science-400" />
        Upload PDF Article
      </h2>

      {uploadedPaper ? (
        <div className="p-4 rounded-lg border border-green-500/30 bg-green-950/20">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-medium text-ink-100 text-sm">
                  {uploadedPaper.title}
                </h3>
                {uploadedPaper.authors.length > 0 && (
                  <p className="text-xs text-ink-400 mt-1">
                    {uploadedPaper.authors.slice(0, 3).join(', ')}
                    {uploadedPaper.authors.length > 3 && ' et al.'}
                  </p>
                )}
                <p className="text-xs text-ink-500 mt-2">
                  Added to papers • Ready for digest
                </p>
              </div>
            </div>
            <button
              onClick={clearUpload}
              className="p-1 hover:bg-ink-700 rounded transition-colors"
            >
              <X className="w-4 h-4 text-ink-400" />
            </button>
          </div>
        </div>
      ) : (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`
            relative border-2 border-dashed rounded-lg p-8 text-center transition-all
            ${isDragging 
              ? 'border-science-400 bg-science-950/30' 
              : 'border-ink-700 hover:border-ink-600'
            }
            ${uploadMutation.isPending ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
          `}
        >
          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileSelect}
            disabled={uploadMutation.isPending}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          
          <div className="flex flex-col items-center gap-3">
            {uploadMutation.isPending ? (
              <>
                <Loader2 className="w-10 h-10 text-science-400 animate-spin" />
                <p className="text-ink-300">Processing PDF...</p>
              </>
            ) : (
              <>
                <FileText className="w-10 h-10 text-ink-500" />
                <div>
                  <p className="text-ink-300">
                    Drop a PDF here or <span className="text-science-400">browse</span>
                  </p>
                  <p className="text-xs text-ink-500 mt-1">
                    Upload research papers, articles, or documents
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
