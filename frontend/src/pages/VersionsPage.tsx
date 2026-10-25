import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { CampaignTabs } from '../components/CampaignTabs'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState, ErrorBox, PageHeader, Spinner } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { useCampaign } from '../hooks/useCampaign'
import { useFetch } from '../hooks/useFetch'
import { useMeta } from '../hooks/useMeta'
import { api, errorMessage } from '../services/api'
import { Page, Version } from '../services/types'
import { fmtDate, humanize } from '../utils/format'

export default function VersionsPage() {
  const { id = '' } = useParams()
  const toast = useToast()
  const meta = useMeta()
  const camp = useCampaign(id)
  const [platform, setPlatform] = useState('')
  const [section, setSection] = useState('')
  const [open, setOpen] = useState<string | null>(null)
  const [restoring, setRestoring] = useState<Version | null>(null)
  const list = useFetch(async () => (await api.get<Page<Version>>(`/campaigns/${id}/versions`, {
    params: { platform: platform || undefined, section: section || undefined, page_size: 100 } })).data, [id, platform, section])

  return (
    <div>
      <PageHeader title={camp.data?.name ?? 'Versions'} subtitle="Full history. Restoring creates a new version; nothing is ever deleted." />
      <CampaignTabs id={id} />
      <div className="mb-4 flex gap-2">
        <select className="input max-w-[12rem]" aria-label="Platform" value={platform} onChange={(e) => setPlatform(e.target.value)}>
          <option value="">All platforms</option>{meta.data && Object.entries(meta.data.platforms).map(([k, p]) => <option key={k} value={k}>{p.label}</option>)}</select>
        <select className="input max-w-[12rem]" aria-label="Section" value={section} onChange={(e) => setSection(e.target.value)}>
          <option value="">All sections</option>{meta.data?.sections.map((s) => <option key={s} value={s}>{humanize(s)}</option>)}</select>
      </div>
      {list.loading && <Spinner />}
      {list.error && <ErrorBox message={list.error} onRetry={list.reload} />}
      {(Array.isArray(list.data?.items) && list.data.items.length === 0) && <EmptyState title="No versions yet" text="Versions appear after you generate or edit content." />}
      <ul className="space-y-2">
        {(Array.isArray(list.data?.items) ? list.data.items : []).map((v) => (
          <li key={v.id} className="card">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm"><b>{humanize(v.section)}</b> · v{v.version_number} · {meta.data?.platforms[v.platform]?.label ?? v.platform}
                <span className="ml-2 rounded bg-slate-100 px-2 py-0.5 text-xs">{humanize(v.source)}</span>
                {v.generation_params?.is_mock && <span className="ml-2 rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">mock</span>}
                <div className="text-xs text-slate-400">{fmtDate(v.created_at)}</div></div>
              <div className="flex gap-2">
                <button className="btn-secondary btn-sm" onClick={() => setOpen(open === v.id ? null : v.id)}>{open === v.id ? 'Hide' : 'View'}</button>
                <button className="btn-secondary btn-sm" onClick={() => setRestoring(v)}>Restore</button>
              </div>
            </div>
            {open === v.id && <pre className="mt-3 max-h-72 overflow-auto rounded bg-slate-50 p-3 text-xs">{JSON.stringify(v.payload, null, 2)}</pre>}
          </li>))}
      </ul>
      <ConfirmDialog open={!!restoring} title="Restore this version?" confirmLabel="Restore" onCancel={() => setRestoring(null)}
        onConfirm={async () => {
          const v = restoring!; setRestoring(null)
          try { await api.post(`/campaigns/${id}/versions/${v.id}/restore`); toast.success(`Restored v${v.version_number} as a new version.`); void list.reload() }
          catch (e) { toast.error(errorMessage(e)) } }}>
        {restoring && <>Version {restoring.version_number} of {humanize(restoring.section)} becomes the current content, saved as a new version.</>}
      </ConfirmDialog>
    </div>
  )
}
