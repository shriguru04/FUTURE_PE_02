import { Component, ErrorInfo, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { humanize } from '../utils/format'

export const Spinner = ({ label = 'Loading…' }: { label?: string }) => (
  <div className="flex items-center gap-2 py-8 text-sm text-slate-500" role="status">
    <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
    {label}
  </div>
)

export const ErrorBox = ({ message, onRetry }: { message: string; onRetry?: () => void }) => (
  <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">
    {message}
    {onRetry && <button className="ml-3 underline" onClick={onRetry}>Retry</button>}
  </div>
)

export const EmptyState = ({ title, text, to, cta }: { title: string; text: string; to?: string; cta?: string }) => (
  <div className="card text-center">
    <h3 className="font-semibold">{title}</h3>
    <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">{text}</p>
    {to && cta && <Link to={to} className="btn-primary mt-4">{cta}</Link>}
  </div>
)

export const PageHeader = ({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) => (
  <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
    <div>
      <h1 className="text-2xl font-bold">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
    </div>
    <div className="flex flex-wrap gap-2">{actions}</div>
  </div>
)

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-slate-100 text-slate-700', in_progress: 'bg-blue-100 text-blue-700',
  ready_for_review: 'bg-amber-100 text-amber-800', approved: 'bg-emerald-100 text-emerald-700',
  archived: 'bg-slate-200 text-slate-500',
}
export const StatusBadge = ({ status }: { status: string }) => (
  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[status] ?? STATUS_COLORS.draft}`}>{humanize(status)}</span>
)

export const Field = ({ label, htmlFor, error, help, children }: {
  label: string; htmlFor: string; error?: string; help?: string; children: ReactNode
}) => (
  <div>
    <label htmlFor={htmlFor} className="label">{label}</label>
    {children}
    {help && !error && <p className="mt-1 text-xs text-slate-500">{help}</p>}
    {error && <p className="err" role="alert">{error}</p>}
  </div>
)

export const ProviderBanner = ({ configured, isMock }: { configured: boolean; isMock: boolean }) => {
  if (!configured) {
    return (
      <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900" role="alert">
        <b>AI provider not configured.</b> Set <code>LLM_API_KEY</code> (plus <code>LLM_BASE_URL</code> and <code>LLM_MODEL</code>)
        in the backend environment, then restart the API. Generation is disabled until then.
      </div>
    )
  }
  return isMock ? (
    <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
      Development mode: the <b>mock provider</b> is active. Output is placeholder text, not real AI generation.
    </div>
  ) : null
}

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error(error, info) }
  render() {
    if (!this.state.failed) return this.props.children
    return (
      <div className="mx-auto mt-20 max-w-md text-center">
        <h1 className="text-xl font-bold">Something went wrong</h1>
        <p className="mt-2 text-sm text-slate-500">An unexpected error occurred in the interface.</p>
        <button className="btn-primary mt-4" onClick={() => window.location.reload()}>Reload</button>
      </div>
    )
  }
}
