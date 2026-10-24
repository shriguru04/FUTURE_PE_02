import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState, ErrorBox, PageHeader, Spinner, StatusBadge } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { useMeta } from '../hooks/useMeta'
import { api, errorMessage } from '../services/api'
import { Campaign, Page } from '../services/types'
import { fmtDate, humanize } from '../utils/format'

export default function CampaignsPage() {
  const toast = useToast()
  const nav = useNavigate()
  const meta = useMeta()
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')
  const [platform, setPlatform] = useState('')
  const [deleting, setDeleting] = useState<Campaign | null>(null)
  const list = useFetch(async () => (await api.get<Page<Campaign>>('/campaigns', {
    params: { q: q || undefined, status: status || undefined, platform: platform || undefined, page_size: 100 } })).data, [q, status, platform])

  const act = async (fn: () => Promise<unknown>, ok: string) => {
    try { await fn(); toast.success(ok); void list.reload() } catch (e) { toast.error(errorMessage(e)) }
  }
  const filtered = q || status || platform

  return (
    <div>
      <PageHeader title="Campaigns" subtitle="Search, filter and manage every campaign." actions={<Link to="/app/campaigns/new" className="btn-primary">New campaign</Link>} />
      <div className="mb-4 flex flex-wrap gap-2">
        <input className="input max-w-xs" placeholder="Search campaigns…" aria-label="Search campaigns" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="input max-w-[11rem]" aria-label="Filter by status" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>{meta.data?.statuses.map((s) => <option key={s} value={s}>{humanize(s)}</option>)}</select>
        <select className="input max-w-[11rem]" aria-label="Filter by platform" value={platform} onChange={(e) => setPlatform(e.target.value)}>
          <option value="">All platforms</option>{meta.data && Object.entries(meta.data.platforms).map(([k, p]) => <option key={k} value={k}>{p.label}</option>)}</select>
      </div>
      {list.loading && <Spinner />}
      {list.error && <ErrorBox message={list.error} onRetry={list.reload} />}
      {!list.loading && list.data?.items.length === 0 && (filtered
        ? <EmptyState title="No matches" text="Try clearing your filters." />
        : <EmptyState title="No campaigns yet" text="Create your first campaign to generate UGC ad content." to="/app/campaigns/new" cta="Create a campaign" />)}
      <div className="space-y-3">
        {list.data?.items.map((c) => (
          <div key={c.id} className="card flex flex-wrap items-center justify-between gap-3">
            <div className="min-w-0">
              <Link to={`/app/campaigns/${c.id}`} className="font-semibold text-brand-700 hover:underline">{c.name}</Link>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                <StatusBadge status={c.status} /><span>{meta.data?.platforms[c.platform]?.label ?? humanize(c.platform)}</span><span>Updated {fmtDate(c.updated_at)}</span>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="btn-secondary btn-sm" onClick={() => nav(`/app/campaigns/${c.id}/generate`)}>Generate</button>
              <button className="btn-secondary btn-sm" onClick={() => act(() => api.post(`/campaigns/${c.id}/duplicate`), 'Campaign duplicated.')}>Duplicate</button>
              {c.status !== 'archived' && <button className="btn-secondary btn-sm" onClick={() => act(() => api.patch(`/campaigns/${c.id}`, { status: 'archived' }), 'Campaign archived.')}>Archive</button>}
              <button className="btn-secondary btn-sm text-red-600" onClick={() => setDeleting(c)}>Delete</button>
            </div>
          </div>
        ))}
      </div>
      <ConfirmDialog open={!!deleting} title="Delete campaign?" onCancel={() => setDeleting(null)}
        onConfirm={async () => { const c = deleting!; setDeleting(null); await act(() => api.delete(`/campaigns/${c.id}`), 'Campaign deleted.') }}>
        <b>{deleting?.name}</b> and all of its generated content, versions and metrics will be permanently deleted.
      </ConfirmDialog>
    </div>
  )
}
