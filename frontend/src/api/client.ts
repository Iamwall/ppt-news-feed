import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api/v1/'

// Backend base URL for static files (images, etc.)
// In development, the Vite proxy handles /static requests
// In production, set VITE_BACKEND_URL to your backend server URL
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''

// Helper to get full image URL
export const getImageUrl = (imagePath: string | null | undefined): string | null => {
  if (!imagePath) return null
  // If it's already a full URL, return as-is
  if (imagePath.startsWith('http')) return imagePath
  // Otherwise, use the path directly (Vite proxy handles /static in dev)
  return `${BACKEND_URL}${imagePath}`
}

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// API functions
export const papersApi = {
  list: (params?: {
    skip?: number
    limit?: number
    source?: string
    min_credibility?: number
  }) => api.get('papers/', { params }),
  
  get: (id: number) => api.get(`papers/${id}`),
  
  delete: (id: number) => api.delete(`papers/${id}`),
  
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('papers/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  }
}

export const digestsApi = {
  list: (params?: { skip?: number; limit?: number; status?: string }) =>
    api.get('digests/', { params }),
  
  get: (id: number) => api.get(`digests/${id}`),
  
  create: (data: {
    name: string
    paper_ids: number[]
    ai_provider?: string
    ai_model?: string
    summary_style?: string
    generate_images?: boolean
  }) => api.post('digests/', data),
  
  regenerate: (id: number) => api.post(`digests/${id}/regenerate`),
  
  delete: (id: number) => api.delete(`digests/${id}`),
}

export const fetchApi = {
  start: (data: {
    sources?: string[]
    keywords?: string[]
    max_results?: number
    days_back?: number
    enable_triage?: boolean
  }) => api.post('fetch/', data),
  
  status: (jobId: number) => api.get(`fetch/status/${jobId}`),
  getStatus: (jobId: number) => api.get(`fetch/status/${jobId}`),
  
  sources: () => api.get('fetch/sources'),
  getSources: () => api.get('fetch/sources'),
}

export const newsletterApi = {
  export: (digestId: number, format: 'html' | 'pdf' | 'markdown') =>
    api.post(`newsletters/${digestId}/export`, { format }, {
      responseType: 'blob',
    }),
  
  preview: (digestId: number) =>
    api.get(`newsletters/${digestId}/preview`, {
      responseType: 'text',
      transformResponse: [(data) => data],  // Prevent JSON parsing
    }),
  
  send: (digestId: number, recipients: string[]) =>
    api.post(`newsletters/${digestId}/send`, { recipients }),
}

export const settingsApi = {
  get: () => api.get('settings/'),

  update: (data: Record<string, unknown>) => api.put('settings/', data),

  getCredibilityWeights: () => api.get('settings/credibility-weights'),

  updateCredibilityWeights: (data: Record<string, number>) =>
    api.put('settings/credibility-weights', data),

  getBranding: () => api.get('settings/branding'),

  getDomains: () => api.get('settings/domains'),

  setActiveDomain: (domainId: string) => api.put(`settings/domain/${domainId}`),
}

export const sourcesApi = {
  list: () => api.get('sources/'),

  create: (data: { 
    name: string
    url: string
    description?: string
    credibility_base_score?: number
    is_peer_reviewed?: boolean
    is_validated?: boolean
    verification_method?: string
  }) => api.post('sources/custom', data),

  update: (id: number, data: { 
    name?: string
    url?: string
    description?: string
    is_active?: boolean
    credibility_base_score?: number
    is_peer_reviewed?: boolean
    is_validated?: boolean
    verification_method?: string
  }) => api.put(`sources/custom/${id}`, data),

  delete: (id: number) => api.delete(`sources/custom/${id}`),

  test: (id: number) => api.post(`sources/custom/${id}/test`),
}



export interface PulsePaper {
  id: number
  title: string
  source: string
  url?: string
  published_date?: string
  is_breaking?: boolean
  breaking_score?: number
  freshness_score?: number
  triage_status?: string
  triage_score?: number
  is_validated_source?: boolean
  fetched_at: string
}

