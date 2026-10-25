import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useLocation } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { EmptyState, ErrorBox, Field, PageHeader, Spinner } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { api, errorMessage } from '../services/api'
import { Campaign, Page, Rates } from '../services/types'
import { fmtMoney, fmtNum, fmtPct } from '../utils/format'

interface Row extends Rates { id: string; metric_date: string; impressions: number | null; reach: number | null; video_views: number | null; clicks: number | null; conversions: number | null; spend: number | null; revenue: number | null }
interface CampAnalytics { has_data: boolean; rows: Row[]; totals: Record<string, number | null>; rates: Rates; disclaimer: string }
interface Overview { disclaimer: string; metrics: { has_data: boolean; totals: Record<string, number | null>; rates: Rates; per_campaign: { campaign_id: string; name: string; totals: Record<string, number | null>; rates: Rates }[] } }

const FIELDS = ['impressions', 'reach', 'video_views', 'clicks', 'conversions', 'spend', 'revenue'] as const
type V = { metric_date: string } & Record<(typeof FIELDS)[number], string>

const Kpi = ({ label, value }: { label: string; value: string }) => (<div className="card py-3"><div className="text-xs text-slate-500">{label}</div><div className="text-xl font-semibold">{value}</div></div>)

export default function AnalyticsPage() {
  const toast = useToast()
  const loc = useLocation() as { state?: { campaignId?: string } }
  const [campaignId, setCampaignId] = useState(loc.state?.campaignId ?? '')
  const campaigns = useFetch(async () => (await api.get<Page<Campaign>>('/campaigns', { params: { page_size: 100 } })).data.items, [])
  const overview = useFetch(async () => (await api.get<Overview>('/analytics/overview')).data, [])
  const detail = useFetch(async () => (campaignId ? (await api.get<CampAnalytics>(`/campaigns/${campaignId}/analytics`)).data : null), [campaignId])
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<V>({ defaultValues: { metric_date: new Date().toISOString().slice(0, 10) } })
  useEffect(() => { if (!campaignId && campaigns.data?.length) setCampaignId(campaigns.data[0].id) }, [campaigns.data, campaignId])

  const submit = async (v: V) => {
    const body: Record<string, unknown> = { metric_date: v.metric_date }
    for (const f of FIELDS) if (v[f] !== '' && v[f] !== undefined) body[f] = Number(v[f])
    try {
      await api.post(`/campaigns/${campaignId}/metrics`, body)
      toast.success('Metrics saved.')
      reset({ metric_date: v.metric_date })
      void detail.reload(); void overview.reload()
    } catch (e) { toast.error(errorMessage(e)) }
  }
  const del = async (rowId: string) => {
    try { await api.delete(`/campaigns/${campaignId}/metrics/${rowId}`); toast.success('Row deleted.'); void detail.reload(); void overview.reload() }
    catch (e) { toast.error(errorMessage(e)) }
  }

  if (campaigns.loading || overview.loading) return <Spinner />
  if (campaigns.error || overview.error) return <ErrorBox message={(campaigns.error ?? overview.error)!} />
  if (!campaigns.data?.length) return <EmptyState title="No campaigns" text="Create a campaign before tracking its performance." to="/app/campaigns/new" cta="New campaign" />
  const o = overview.data!
  const d = detail.data

  return (
    <div>
      <PageHeader title="Analytics" subtitle="Performance you enter yourself." />
      <div className="mb-6 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900" role="note">{o.disclaimer}</div>

      <h2 className="mb-2 font-semibold">All campaigns</h2>
      {!o.metrics.has_data ? <p className="mb-6 text-sm text-slate-500">No metrics entered yet. Missing values show as “—”, never as zero.</p> : (
        <div className="mb-6">
          <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-5">
            <Kpi label="Impressions" value={fmtNum(o.metrics.totals.impressions)} /><Kpi label="CTR" value={fmtPct(o.metrics.rates.ctr)} />
            <Kpi label="Conversion rate" value={fmtPct(o.metrics.rates.conversion_rate)} /><Kpi label="CPA" value={fmtMoney(o.metrics.rates.cpa)} />
            <Kpi label="ROAS" value={fmtNum(o.metrics.rates.roas, 2)} />
          </div>
          <div className="card h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={o.metrics.per_campaign.map((c) => ({ name: c.name, CTR: c.rates.ctr, 'Conv. rate': c.rates.conversion_rate }))}>
            <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" fontSize={11} /><YAxis fontSize={11} unit="%" /><Tooltip /><Legend />
            <Bar dataKey="CTR" fill="#4f46e5" /><Bar dataKey="Conv. rate" fill="#10b981" /></BarChart></ResponsiveContainer></div>
        </div>)}

      <h2 className="mb-2 font-semibold">Campaign detail</h2>
      <select className="input mb-4 max-w-sm" aria-label="Campaign" value={campaignId} onChange={(e) => setCampaignId(e.target.value)}>
        {campaigns.data.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select>

      <form onSubmit={handleSubmit(submit)} className="card mb-4" noValidate>
        <h3 className="mb-3 font-medium">Add daily metrics (manual entry)</h3>
        <div className="grid gap-3 sm:grid-cols-4">
          <Field label="Date *" htmlFor="metric_date" error={errors.metric_date?.message}><input id="metric_date" type="date" className="input" {...register('metric_date', { required: 'Date is required.' })} /></Field>
          {FIELDS.map((f) => (
            <Field key={f} label={f.replace('_', ' ')} htmlFor={f} error={errors[f]?.message}>
              <input id={f} type="number" min="0" step={f === 'spend' || f === 'revenue' ? '0.01' : '1'} className="input"
                {...register(f, { validate: (x) => x === '' || Number(x) >= 0 || 'Must be ≥ 0' })} /></Field>))}
        </div>
        <p className="mt-2 text-xs text-slate-500">Leave unknown values blank. Clicks cannot exceed impressions.</p>
        <button className="btn-primary mt-3" disabled={isSubmitting}>{isSubmitting ? 'Saving…' : 'Add metrics'}</button>
      </form>

      {detail.loading ? <Spinner /> : d && d.has_data ? (
        <>
          <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-5">
            <Kpi label="CTR" value={fmtPct(d.rates.ctr)} /><Kpi label="Conv. rate" value={fmtPct(d.rates.conversion_rate)} /><Kpi label="CPC" value={fmtMoney(d.rates.cpc)} />
            <Kpi label="CPA" value={fmtMoney(d.rates.cpa)} /><Kpi label="ROAS" value={fmtNum(d.rates.roas, 2)} />
          </div>
          <div className="card mb-4 h-64"><ResponsiveContainer width="100%" height="100%"><LineChart data={d.rows}>
            <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="metric_date" fontSize={11} /><YAxis fontSize={11} /><Tooltip /><Legend />
            <Line type="monotone" dataKey="clicks" stroke="#4f46e5" connectNulls={false} /><Line type="monotone" dataKey="conversions" stroke="#10b981" connectNulls={false} /></LineChart></ResponsiveContainer></div>
          <div className="card overflow-x-auto p-0"><table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr>{['Date', 'Impr.', 'Clicks', 'Conv.', 'Spend', 'Revenue', 'CTR', 'CPC', 'CPA', 'ROAS', ''].map((h) => <th key={h} className="px-3 py-2">{h}</th>)}</tr></thead>
            <tbody>{d.rows.map((r) => (
              <tr key={r.id} className="border-t border-slate-100"><td className="px-3 py-2">{r.metric_date}</td><td className="px-3">{fmtNum(r.impressions)}</td><td className="px-3">{fmtNum(r.clicks)}</td>
                <td className="px-3">{fmtNum(r.conversions)}</td><td className="px-3">{fmtMoney(r.spend)}</td><td className="px-3">{fmtMoney(r.revenue)}</td><td className="px-3">{fmtPct(r.ctr)}</td>
                <td className="px-3">{fmtMoney(r.cpc)}</td><td className="px-3">{fmtMoney(r.cpa)}</td><td className="px-3">{fmtNum(r.roas, 2)}</td>
                <td className="px-3"><button className="text-xs text-red-600 underline" onClick={() => del(r.id)}>Delete</button></td></tr>))}</tbody></table></div>
        </>
      ) : <p className="text-sm text-slate-500">No metrics for this campaign yet.</p>}
    </div>
  )
}
