export interface Author {
  name: string
  affiliation?: string
  h_index?: number
}

export interface Paper {
  id: number
  title: string
  abstract: string | null
  journal: string | null
  doi: string | null
  url: string | null
  source: string
  source_id?: string
  published_date: string | null
  fetched_at?: string
  
  // Metrics
  citations?: number
  influential_citations?: number
  credibility_score: number | null
  
  // AI Generated
  summary_headline: string | null
  summary_takeaway: string | null
  summary_why_matters?: string | null
  key_takeaways?: string[] | null
  credibility_note?: string | null
  tags: string[] | null
  image_path?: string | null
  
  // Flags
  is_preprint: boolean
  is_peer_reviewed?: boolean
  
  authors: Author[]
}

export interface DigestPaper {
  id: number
  paper_id: number
  digest_id: number
  paper: Paper
}

export type DigestStatus = 'created' | 'pending' | 'processing' | 'completed' | 'failed'

export interface Digest {
  id: number
  name: string
  status: DigestStatus
  created_at: string
  intro_text?: string | null
  connecting_narrative?: string | null
  conclusion_text?: string | null
  summary_image_path?: string | null
  error_message?: string | null
  digest_papers: DigestPaper[]

  // Settings used
  ai_provider?: string
  ai_model?: string
  summary_style?: string
}

export interface Source {
  id: string
  name: string
  category: string
  description?: string
  type: string
  requiresApiKey?: boolean
  isCustom?: boolean
  isEnabled?: boolean
  url?: string
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  [key: string]: unknown
}

// Specific responses based on existing code usage
export interface PapersResponse {
  papers: Paper[]
  total: number
}

export interface DigestsResponse {
  digests: Digest[]
  total: number
}

export interface SourcesResponse {
    sources: Source[]
    domainId: string
}
