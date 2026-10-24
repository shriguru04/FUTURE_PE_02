import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { CampaignTabs } from '../components/CampaignTabs'
import { EmptyState, PageHeader, Spinner } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { useCampaign } from '../hooks/useCampaign'
import { useFetch } from '../hooks/useFetch'
import { useMeta } from '../hooks/useMeta'
import { api, errorMessage } from '../services/api'
import { Content } from '../services/types'

const FORMATS = [['pdf', 'PDF'], ['md', 'Markdown'], ['txt', 'Plain text'], ['json', 'JSON']] as const

export default function ExportPage() {
  const { id = '' } = useParams()
  const toast = useToast()
  const meta = useMeta()
  const camp = useCampaign(id)
  const content = useFetch(async () => (await api.get<Content[]>(`/campaigns/${id}/content`)).data, [id])
  const [format, setFormat] = useState<string>('pdf')
  const [selected, setSelected] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const available = [...new Set((content.data ?? []).map((c) => c.platform))]
  useEffect(() => setSelected(available), [content.data]) // eslint-disable-line react-hooks/exhaustive-deps

  if (content.loading) return <Spinner />

  const download = async () => {
    setBusy(true)
    try {
      const r = await api.post(`/campaigns/${id}/export`, { format, platforms: selected }, { responseType: 'blob' })
      const name = /filename="([^"]+)"/.exec(r.headers['content-disposition'] ?? '')?.[1] ?? `campaign.${format}`
      const url = URL.createObjectURL(r.data)
      const a = document.createElement('a')
      a.href = url; a.download = name; a.click()
      URL.revokeObjectURL(url)
      toast.success(`Exported ${name}`)
    } catch (e) {
      toast.error(errorMessage(e))
    } finally { setBusy(false) }
  }

  return (
    <div>
      <PageHeader title={camp.data?.name ?? 'Export'} subtitle="Download the campaign pack, including review notes and a pre-publication checklist." />
      <CampaignTabs id={id} />
      {available.length === 0 ? <EmptyState title="Nothing to export" text="Generate content first." to={`/app/campaigns/${id}/generate`} cta="Generate" /> : (
        <div className="card max-w-xl space-y-4">
          <fieldset><legend className="label">Format</legend>
            <div className="flex flex-wrap gap-3">{FORMATS.map(([k, l]) => (
              <label key={k} className="flex items-center gap-2 text-sm"><input type="radio" name="format" checked={format === k} onChange={() => setFormat(k)} />{l}</label>))}</div></fieldset>
          <fieldset><legend className="label">Platforms</legend>
            <div className="flex flex-wrap gap-3">{available.map((p) => (
              <label key={p} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={selected.includes(p)}
                onChange={() => setSelected(selected.includes(p) ? selected.filter((x) => x !== p) : [...selected, p])} />{meta.data?.platforms[p]?.label ?? p}</label>))}</div></fieldset>
          <p className="text-xs text-slate-500">PDF export covers Latin-script text only.</p>
          <button className="btn-primary" onClick={download} disabled={busy || selected.length === 0}>{busy ? 'Preparing…' : 'Download'}</button>
        </div>)}
    </div>
  )
}
