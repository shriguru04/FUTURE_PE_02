import { NavLink } from 'react-router-dom'

const TABS = [['', 'Overview'], ['generate', 'Generate'], ['editor', 'Editor'], ['versions', 'Versions'], ['export', 'Export']] as const

export function CampaignTabs({ id }: { id: string }) {
  return (
    <nav className="mb-6 flex gap-1 overflow-x-auto border-b border-slate-200" aria-label="Campaign sections">
      {TABS.map(([path, label]) => (
        <NavLink key={path} end={path === ''} to={`/app/campaigns/${id}${path ? '/' + path : ''}`}
          className={({ isActive }) => `whitespace-nowrap border-b-2 px-4 py-2 text-sm ${isActive ? 'border-brand-600 font-semibold text-brand-700' : 'border-transparent text-slate-500 hover:text-slate-800'}`}>
          {label}
        </NavLink>
      ))}
      <NavLink to="/app/analytics" state={{ campaignId: id }} className="whitespace-nowrap border-b-2 border-transparent px-4 py-2 text-sm text-slate-500 hover:text-slate-800">Analytics</NavLink>
    </nav>
  )
}
