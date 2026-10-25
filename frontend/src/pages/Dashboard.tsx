import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { EmptyState, ErrorBox, PageHeader, Spinner, StatusBadge } from '../components/ui'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'
import { Campaign, Rates } from '../services/types'
import { fmtDate, fmtNum, fmtPct, humanize } from '../utils/format'

interface Overview {
  campaign_counts: { total: number; by_status: Record<string, number> }
  platform_distribution: Record<string, number>
  recent_campaigns: Campaign[]
  draft_campaigns: Campaign[]
  recent_generations: { campaign_id: string; campaign_name: string; platform: string; kind: string; section: string | null; created_at: string }[]
  metrics: { has_data: boolean; totals: Record<string, number | null>; rates: Rates }
}

const CampaignList = ({ items }: { items: Campaign[] }) => (
  <ul className="divide-y divide-slate-100">
    {items.map((c) => (
      <li key={c.id} className="flex items-center justify-between py-2">
        <Link className="font-medium text-brand-700 hover:underline" to={`/app/campaigns/${c.id}`}>{c.name}</Link>
        <StatusBadge status={c.status} />
      </li>
    ))}
  </ul>
)

export default function Dashboard() {
  const { data, loading, error, reload } = useFetch(async () => (await api.get<Overview>('/analytics/overview')).data, [])
  if (loading) return <Spinner />
  if (error || !data) return <ErrorBox message={error ?? 'Failed to load.'} onRetry={reload} />
  const platformDistribution = data.platform_distribution && typeof data.platform_distribution === 'object' ? data.platform_distribution : {}
  const chart = Object.entries(platformDistribution).map(([k, v]) => ({ name: humanize(k), campaigns: v }))
  const counts = data.campaign_counts?.by_status ?? {}
  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Your campaigns at a glance." actions={<Link to="/app/campaigns/new" className="btn-primary">New campaign</Link>} />
      {(data.campaign_counts?.total ?? 0) === 0 ? (
        <EmptyState title="No campaigns yet" text="Create a brand and product, then generate your first campaign pack." to="/app/campaigns/new" cta="Create a campaign" />
      ) : (
        <>
          <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-5">
            <div className="card"><div className="text-2xl font-bold">{data.campaign_counts?.total ?? 0}</div><div className="text-xs text-slate-500">Total</div></div>
            {['draft', 'in_progress', 'ready_for_review', 'approved'].map((s) => (
              <div key={s} className="card"><div className="text-2xl font-bold">{counts[s] ?? 0}</div><div className="text-xs text-slate-500">{humanize(s)}</div></div>
            ))}
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <section className="card"><h2 className="mb-2 font-semibold">Recent campaigns</h2><CampaignList items={Array.isArray(data.recent_campaigns) ? data.recent_campaigns : []} /></section>
            <section className="card"><h2 className="mb-2 font-semibold">Drafts</h2>
              {(Array.isArray(data.draft_campaigns) ? data.draft_campaigns : []).length ? <CampaignList items={Array.isArray(data.draft_campaigns) ? data.draft_campaigns : []} /> : <p className="text-sm text-slate-500">No drafts.</p>}</section>
            <section className="card"><h2 className="mb-2 font-semibold">Recently generated</h2>
              {(Array.isArray(data.recent_generations) ? data.recent_generations : []).length === 0 ? <p className="text-sm text-slate-500">Nothing generated yet.</p> : (
                <ul className="space-y-1 text-sm">{(Array.isArray(data.recent_generations) ? data.recent_generations : []).map((g, i) => (
                  <li key={i}><Link className="text-brand-700 hover:underline" to={`/app/campaigns/${g.campaign_id}/editor`}>{g.campaign_name}</Link>
                    {' '}· {humanize(g.platform)}{g.section ? ` · ${humanize(g.section)}` : ''} <span className="text-slate-400">{fmtDate(g.created_at)}</span></li>))}</ul>)}</section>
            <section className="card"><h2 className="mb-2 font-semibold">Platform distribution</h2>
              <div className="h-48"><ResponsiveContainer width="100%" height="100%"><BarChart data={chart}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" fontSize={11} /><YAxis allowDecimals={false} fontSize={11} /><Tooltip />
                <Bar dataKey="campaigns" fill="#4f46e5" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div></section>
            <section className="card lg:col-span-2"><h2 className="mb-1 font-semibold">Performance summary</h2>
              <p className="mb-3 text-xs text-slate-500">Based only on metrics you entered manually. Not connected to any ad platform.</p>
              {data.metrics?.has_data ? (
                <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-5">
                  {([['Impressions', fmtNum(data.metrics?.totals?.impressions)], ['CTR', fmtPct(data.metrics?.rates?.ctr)], ['Conv. rate', fmtPct(data.metrics?.rates?.conversion_rate)],
                    ['CPC', fmtNum(data.metrics?.rates?.cpc, 2)], ['ROAS', fmtNum(data.metrics?.rates?.roas, 2)]] as const).map(([k, v]) => (
                    <div key={k}><div className="text-xs text-slate-500">{k}</div><div className="text-lg font-semibold">{v}</div></div>))}
                </div>
              ) : <p className="text-sm text-slate-500">No metrics entered yet. <Link className="text-brand-700 underline" to="/app/analytics">Add some</Link>.</p>}
            </section>
          </div>
        </>
      )}
    </div>
  )
}
