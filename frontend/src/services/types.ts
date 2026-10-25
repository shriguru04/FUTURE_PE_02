export interface User { id: string; email: string; display_name: string; created_at: string }
export interface Page<T> { items: T[]; total: number; page: number; page_size: number }
export interface Brand {
  id: string; name: string; category: string; description: string; target_audience: string; voice: string
  language: string; writing_style: string; messaging_guidelines: string; avoid_terms: string[]
  website_url: string; default_cta: string
}
export interface Product {
  id: string; brand_id: string; name: string; description: string; features: string[]; benefits: string[]
  price: number | null; intended_audience: string; supported_claims: string[]; limitations: string
  offer_details: string; cta: string
}
export interface Campaign {
  id: string; name: string; brand_id: string; product_id: string | null; objective: string
  platform: string; status: string; notes: string; settings: Record<string, any>
  created_at: string; updated_at: string
}
export interface Content { id: string; platform: string; section: string; payload: any; current_version: number; updated_at: string }
export interface Version {
  id: string; content_id: string; platform: string; section: string; version_number: number
  payload: any; source: string; generation_params: any; created_at: string
}
export interface PlatformInfo {
  label: string; checklist: string[]; duration_seconds: { min: number; max: number; suggested: number }
}
export interface Meta {
  platforms: Record<string, PlatformInfo>; universal_checklist: string[]; content_formats: string[]
  statuses: string[]; sections: string[]
  llm: { configured: boolean; provider: string; model: string; is_mock: boolean }
}
export interface Rates { ctr: number | null; conversion_rate: number | null; cpc: number | null; cpa: number | null; roas: number | null }
export interface GenerateResponse {
  provider: string; model: string; is_mock: boolean
  results: { platform: string; status: 'succeeded' | 'failed'; error_code?: string; error_message?: string }[]
}
