import axios from 'axios'

export class ApiError extends Error {
  status: number
  code: string
  details: unknown
  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

export const api = axios.create({ baseURL: '/api/v1', withCredentials: true, timeout: 120000 })

api.interceptors.response.use(
  (r) => r,
  async (err) => {
    const status: number = err.response?.status ?? 0
    let data = err.response?.data
    if (typeof Blob !== 'undefined' && data instanceof Blob) {
      try { data = JSON.parse(await data.text()) } catch { data = undefined }  // blob responses (exports)
    }
    const body = data?.error
    const url: string = err.config?.url ?? ''
    if (status === 401 && !url.startsWith('/auth/')) window.dispatchEvent(new Event('auth:expired'))
    const message = body?.message ?? (status === 0 ? 'Cannot reach the server. Check your connection.' : 'Something went wrong.')
    return Promise.reject(new ApiError(status, body?.code ?? 'network_error', message, body?.details))
  },
)

export const errorMessage = (e: unknown): string => (e instanceof Error ? e.message : 'Something went wrong.')
