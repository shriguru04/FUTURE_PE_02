import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { CampaignTabs } from '../components/CampaignTabs'
import { SectionEditor } from '../components/SectionEditors'
import { EmptyState, ErrorBox, PageHeader, ProviderBanner, Spinner } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { useCampaign } from '../hooks/useCampaign'
import { useFetch } from '../hooks/useFetch'
import { useMeta } from '../hooks/useMeta'
import { api, errorMessage } from '../services/api'
import { Content } from '../services/types'
import { humanize } from '../utils/format'

const ORDER = ['summary', 'hooks', 'primary_script', 'alt_scripts', 'caption', 'ctas', 'hashtags', 'variations', 'adaptation', 'claims_review']

export default function EditorPage() {
  const { id = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const toast = useToast()
  const meta = useMeta()
  const camp = useCampaign(id)
  const content = useFetch(async () => (await api.get<Content[]>(`/campaigns/${id}/content`)).data, [id])
  const [drafts, setDrafts] = useState<Record<string, any>>({})
  const [instr, setInstr] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState<string | null>(null)

  const platforms = useMemo(() => [...new Set((content.data ?? []).map((c) => c.platform))], [content.data])
  const platform = params.get('platform') && platforms.includes(params.get('platform')!) ? params.get('platform')! : platforms[0]
  useEffect(() => setDrafts({}), [platform])

  if (content.loading || camp.loading || meta.loading) return <Spinner />
  if (content.error || camp.error) return <ErrorBox message={(content.error ?? camp.error)!} onRetry={content.reload} />
  const llm = meta.data?.llm
  const sections = (content.data ?? []).filter((c) => c.platform === platform).sort((a, b) => ORDER.indexOf(a.section) - ORDER.indexOf(b.section))

  const save = async (c: Content) => {
    setBusy(c.section)
    try {
      await api.patch(`/campaigns/${id}/content`, { platform: c.platform, section: c.section, payload: drafts[c.section] })
      toast.success(`${humanize(c.section)} saved as a new version.`)
      setDrafts(({ [c.section]: _, ...rest }) => rest)
      await content.reload()
    } catch (e) { toast.error(errorMessage(e)) } finally { setBusy(null) }
  }
  const regenerate = async (c: Content) => {
    setBusy(c.section)
    try {
      await api.post(`/campaigns/${id}/regenerate-section`, { platform: c.platform, section: c.section, instruction: instr[c.section] ?? '' })
      toast.success(`${humanize(c.section)} regenerated.`)
      setDrafts(({ [c.section]: _, ...rest }) => rest)
      await content.reload()
    } catch (e) { toast.error(errorMessage(e)) } finally { setBusy(null) }
  }

  return (
    <div>
      <PageHeader title={camp.data?.name ?? 'Editor'} subtitle="Edit generated content. Every save creates a restorable version." />
      <CampaignTabs id={id} />
      {llm && <ProviderBanner configured={llm.configured} isMock={llm.is_mock} />}
      {platforms.length === 0 ? (
        <EmptyState title="Nothing to edit yet" text="Generate a campaign pack first." to={`/app/campaigns/${id}/generate`} cta="Generate content" />
      ) : (
        <>
          <div className="mb-4 flex flex-wrap gap-2" role="tablist">
            {platforms.map((p) => (
              <button key={p} role="tab" aria-selected={p === platform} onClick={() => setParams({ platform: p })}
                className={p === platform ? 'btn-primary btn-sm' : 'btn-secondary btn-sm'}>{meta.data?.platforms[p]?.label ?? p}</button>))}
            <Link to={`/app/campaigns/${id}/generate`} className="btn-secondary btn-sm">+ Add platform</Link>
          </div>
          <div className="space-y-4">
            {sections.map((c) => {
              const dirty = c.section in drafts && JSON.stringify(drafts[c.section]) !== JSON.stringify(c.payload)
              return (
                <section key={c.id} className="card" aria-label={humanize(c.section)}>
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <h2 className="font-semibold">{humanize(c.section)} <span className="ml-1 text-xs font-normal text-slate-400">v{c.current_version}</span></h2>
                    <div className="flex flex-wrap items-center gap-2">
                      <input className="input w-48 py-1 text-xs" placeholder="Regenerate instruction (optional)" aria-label={`Instruction for ${humanize(c.section)}`}
                        value={instr[c.section] ?? ''} onChange={(e) => setInstr({ ...instr, [c.section]: e.target.value })} />
                      <button className="btn-secondary btn-sm" disabled={!!busy || !llm?.configured} onClick={() => regenerate(c)}>{busy === c.section ? 'Working…' : 'Regenerate'}</button>
                    </div>
                  </div>
                  <SectionEditor section={c.section} value={drafts[c.section] ?? c.payload} onChange={(v) => setDrafts({ ...drafts, [c.section]: v })} />
                  <div className="mt-3 flex gap-2">
                    <button className="btn-primary btn-sm" disabled={!dirty || !!busy} onClick={() => save(c)}>Save version</button>
                    {dirty && <button className="btn-secondary btn-sm" onClick={() => setDrafts(({ [c.section]: _, ...r }) => r)}>Discard</button>}
                    {dirty && <span className="self-center text-xs text-amber-700">Unsaved changes</span>}
                  </div>
                </section>)
            })}
          </div>
        </>
      )}
    </div>
  )
}
