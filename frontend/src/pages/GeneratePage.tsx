import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useParams } from 'react-router-dom'
import { CampaignTabs } from '../components/CampaignTabs'
import { ErrorBox, Field, PageHeader, ProviderBanner, Spinner } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { useCampaign } from '../hooks/useCampaign'
import { useMeta } from '../hooks/useMeta'
import { api, errorMessage } from '../services/api'
import { GenerateResponse } from '../services/types'
import { humanize } from '../utils/format'

interface V {
  content_format: string; duration_seconds: number; tone: string; target_audience: string; offer: string
  main_problem: string; desired_cta: string; num_hooks: number; num_variations: number
  reference_content: string; language: string
}

export default function GeneratePage() {
  const { id = '' } = useParams()
  const toast = useToast()
  const meta = useMeta()
  const camp = useCampaign(id)
  const [platforms, setPlatforms] = useState<string[]>([])
  const [result, setResult] = useState<GenerateResponse | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<V>({
    defaultValues: { content_format: 'problem_solution', duration_seconds: 30, num_hooks: 5, num_variations: 3 },
  })
  useEffect(() => { if (camp.data) setPlatforms([camp.data.platform]) }, [camp.data])

  if (camp.loading || meta.loading) return <Spinner />
  if (camp.error || !camp.data || !meta.data) return <ErrorBox message={camp.error ?? meta.error ?? 'Failed to load'} />
  const llm = meta.data.llm

  const onSubmit = async (v: V) => {
    setResult(null); setFailure(null)
    try {
      const { data } = await api.post<GenerateResponse>(`/campaigns/${id}/generate`, {
        ...v, platforms, duration_seconds: Number(v.duration_seconds), num_hooks: Number(v.num_hooks), num_variations: Number(v.num_variations) })
      setResult(data)
      const failed = data.results.filter((r) => r.status === 'failed').length
      failed ? toast.error(`${failed} platform(s) failed.`) : toast.success('Content generated and saved.')
    } catch (e) { setFailure(errorMessage(e)); toast.error(errorMessage(e)) }
  }
  const toggle = (p: string) => setPlatforms((cur) => (cur.includes(p) ? cur.filter((x) => x !== p) : [...cur, p]))

  return (
    <div>
      <PageHeader title={camp.data.name} subtitle="Generate campaign content" />
      <CampaignTabs id={id} />
      <ProviderBanner configured={llm.configured} isMock={llm.is_mock} />
      <form onSubmit={handleSubmit(onSubmit)} className="card max-w-3xl space-y-4" noValidate>
        <fieldset><legend className="label">Platforms *</legend>
          <div className="flex flex-wrap gap-3">{Object.entries(meta.data.platforms).map(([k, p]) => (
            <label key={k} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={platforms.includes(k)} onChange={() => toggle(k)} />{p.label}</label>))}</div>
          {platforms.length === 0 && <p className="err">Select at least one platform.</p>}</fieldset>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Content format" htmlFor="content_format"><select id="content_format" className="input" {...register('content_format')}>
            {meta.data.content_formats.map((f) => <option key={f} value={f}>{humanize(f)}</option>)}</select></Field>
          <Field label="Preferred duration (seconds)" htmlFor="duration_seconds" error={errors.duration_seconds?.message}>
            <input id="duration_seconds" type="number" className="input" {...register('duration_seconds', { min: { value: 5, message: 'Min 5.' }, max: { value: 180, message: 'Max 180.' }, required: 'Required.' })} /></Field>
          <Field label="Tone of voice" htmlFor="tone"><input id="tone" className="input" {...register('tone')} /></Field>
          <Field label="Language" htmlFor="language" help="Blank = brand default"><input id="language" className="input" {...register('language')} /></Field>
          <Field label="Hooks" htmlFor="num_hooks" error={errors.num_hooks?.message}><input id="num_hooks" type="number" className="input" {...register('num_hooks', { min: { value: 1, message: '1–10' }, max: { value: 10, message: '1–10' }, required: 'Required.' })} /></Field>
          <Field label="Test variations" htmlFor="num_variations" error={errors.num_variations?.message}><input id="num_variations" type="number" className="input" {...register('num_variations', { min: { value: 1, message: '1–5' }, max: { value: 5, message: '1–5' }, required: 'Required.' })} /></Field>
        </div>
        <Field label="Target audience (overrides brand)" htmlFor="target_audience"><textarea id="target_audience" rows={2} className="input" {...register('target_audience')} /></Field>
        <Field label="Main problem to address" htmlFor="main_problem"><textarea id="main_problem" rows={2} className="input" {...register('main_problem')} /></Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Campaign offer" htmlFor="offer"><input id="offer" className="input" {...register('offer')} /></Field>
          <Field label="Desired CTA" htmlFor="desired_cta"><input id="desired_cta" className="input" {...register('desired_cta')} /></Field>
        </div>
        <Field label="Reference content (optional)" htmlFor="reference_content" error={errors.reference_content?.message} help="Treated as untrusted inspiration only. Max 5000 characters.">
          <textarea id="reference_content" rows={3} className="input" {...register('reference_content', { maxLength: { value: 5000, message: 'Max 5000 characters.' } })} /></Field>
        <button className="btn-primary" disabled={isSubmitting || platforms.length === 0 || !llm.configured}>
          {isSubmitting ? 'Generating… this can take up to a minute' : 'Generate campaign pack'}</button>
      </form>
      {failure && <div className="mt-4 max-w-3xl"><ErrorBox message={failure} /></div>}
      {result && (
        <div className="card mt-4 max-w-3xl">
          <h2 className="font-semibold">Results {result.is_mock && <span className="ml-2 rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">MOCK output</span>}</h2>
          <ul className="mt-2 space-y-1 text-sm">{result.results.map((r) => (
            <li key={r.platform}>{meta.data!.platforms[r.platform]?.label}: {r.status === 'succeeded'
              ? <Link className="text-brand-700 underline" to={`/app/campaigns/${id}/editor?platform=${r.platform}`}>open in editor</Link>
              : <span className="text-red-600">failed – {r.error_message}</span>}</li>))}</ul>
          <p className="mt-3 text-xs text-slate-500">Model: {result.model}. AI-generated drafts are not verified facts: review the claims check before publishing.</p>
        </div>
      )}
    </div>
  )
}
