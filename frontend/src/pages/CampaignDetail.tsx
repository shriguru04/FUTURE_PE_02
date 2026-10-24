import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { CampaignTabs } from '../components/CampaignTabs'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { ErrorBox, Field, PageHeader, Spinner, StatusBadge } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { useCampaign } from '../hooks/useCampaign'
import { useFetch } from '../hooks/useFetch'
import { useMeta } from '../hooks/useMeta'
import { api, errorMessage } from '../services/api'
import { Content } from '../services/types'
import { humanize } from '../utils/format'

interface V { name: string; objective: string; status: string; platform: string; notes: string }

export default function CampaignDetail() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const toast = useToast()
  const meta = useMeta()
  const camp = useCampaign(id)
  const content = useFetch(async () => (await api.get<Content[]>(`/campaigns/${id}/content`)).data, [id])
  const [confirm, setConfirm] = useState(false)
  const { register, handleSubmit, reset, formState: { errors, isSubmitting, isDirty } } = useForm<V>()
  useEffect(() => { if (camp.data) reset(camp.data) }, [camp.data, reset])

  if (camp.loading) return <Spinner />
  if (camp.error || !camp.data) return <ErrorBox message={camp.error ?? 'Not found'} />
  const c = camp.data
  const byPlatform = (content.data ?? []).reduce<Record<string, number>>((a, x) => ({ ...a, [x.platform]: (a[x.platform] ?? 0) + 1 }), {})

  const save = async (v: V) => {
    try { camp.setData((await api.patch(`/campaigns/${id}`, { name: v.name, objective: v.objective, status: v.status, platform: v.platform, notes: v.notes })).data); toast.success('Campaign updated.') }
    catch (e) { toast.error(errorMessage(e)) }
  }

  return (
    <div>
      <PageHeader title={c.name} subtitle={meta.data?.platforms[c.platform]?.label} actions={<StatusBadge status={c.status} />} />
      <CampaignTabs id={id} />
      <div className="grid gap-4 lg:grid-cols-3">
        <form onSubmit={handleSubmit(save)} className="card space-y-4 lg:col-span-2" noValidate>
          <h2 className="font-semibold">Campaign details</h2>
          <Field label="Name *" htmlFor="name" error={errors.name?.message}><input id="name" className="input" {...register('name', { required: 'Name is required.' })} /></Field>
          <Field label="Objective" htmlFor="objective"><textarea id="objective" rows={3} className="input" {...register('objective')} /></Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Status" htmlFor="status"><select id="status" className="input" {...register('status')}>{meta.data?.statuses.map((s) => <option key={s} value={s}>{humanize(s)}</option>)}</select></Field>
            <Field label="Platform" htmlFor="platform"><select id="platform" className="input" {...register('platform')}>{meta.data && Object.entries(meta.data.platforms).map(([k, p]) => <option key={k} value={k}>{p.label}</option>)}</select></Field>
          </div>
          <Field label="Notes" htmlFor="notes"><textarea id="notes" rows={3} className="input" {...register('notes')} /></Field>
          <button className="btn-primary" disabled={isSubmitting || !isDirty}>{isSubmitting ? 'Saving…' : 'Save changes'}</button>
        </form>
        <div className="space-y-4">
          <section className="card"><h2 className="mb-2 font-semibold">Generated content</h2>
            {content.loading ? <Spinner /> : Object.keys(byPlatform).length === 0 ? (
              <p className="text-sm text-slate-500">Nothing generated yet. <Link className="text-brand-700 underline" to={`/app/campaigns/${id}/generate`}>Generate content</Link></p>
            ) : <ul className="space-y-1 text-sm">{Object.entries(byPlatform).map(([p, n]) => (
              <li key={p}><Link className="text-brand-700 hover:underline" to={`/app/campaigns/${id}/editor?platform=${p}`}>{meta.data?.platforms[p]?.label ?? p}</Link> · {n} sections</li>))}</ul>}
          </section>
          <section className="card space-y-2"><h2 className="font-semibold">Actions</h2>
            <button className="btn-secondary w-full" onClick={async () => { try { const r = await api.post(`/campaigns/${id}/duplicate`); toast.success('Duplicated.'); nav(`/app/campaigns/${r.data.id}`) } catch (e) { toast.error(errorMessage(e)) } }}>Duplicate</button>
            {c.status !== 'archived' && <button className="btn-secondary w-full" onClick={async () => { try { camp.setData((await api.patch(`/campaigns/${id}`, { status: 'archived' })).data); toast.success('Archived.') } catch (e) { toast.error(errorMessage(e)) } }}>Archive</button>}
            <button className="btn-danger w-full" onClick={() => setConfirm(true)}>Delete campaign</button>
          </section>
        </div>
      </div>
      <ConfirmDialog open={confirm} title="Delete campaign?" onCancel={() => setConfirm(false)}
        onConfirm={async () => { try { await api.delete(`/campaigns/${id}`); toast.success('Campaign deleted.'); nav('/app/campaigns') } catch (e) { toast.error(errorMessage(e)); setConfirm(false) } }}>
        All generated content, versions and metrics will be permanently deleted.
      </ConfirmDialog>
    </div>
  )
}
