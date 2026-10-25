import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const FEATURES = [
  ['Campaign packs', 'Hooks, scene-by-scene scripts, voice-over, captions, CTAs and hashtags in one structured pack.'],
  ['Platform-aware', 'Adapt one campaign for Reels, Facebook video, Shorts, TikTok-style and website video.'],
  ['Claims review', 'Every claim is checked against the facts you supplied. Unsupported ones are flagged, not hidden.'],
  ['Versioned editing', 'Edit anything, regenerate one section, and restore any earlier version without losing history.'],
  ['Export', 'Download campaign packs as TXT, Markdown, JSON or PDF.'],
  ['Your own metrics', 'Enter results by hand and track CTR, CPC, CPA and ROAS. No fake live-analytics claims.'],
]

export default function Landing() {
  const { user } = useAuth()
  return (
    <div>
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
        <span className="text-xl font-bold text-brand-700">AdCraft AI</span>
        <nav className="flex gap-3">
          {user ? <Link to="/app" className="btn-primary">Open app</Link> : <>
            <Link to="/login" className="btn-secondary">Log in</Link>
            <Link to="/register" className="btn-primary">Get started</Link></>}
        </nav>
      </header>
      <section className="mx-auto max-w-4xl px-4 py-16 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">UGC-style ad campaigns, drafted in minutes</h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          Describe your brand and product. AdCraft AI drafts hooks, scripts and captions that stay on-brand and stick to the claims you can actually support.
        </p>
        <Link to={user ? '/app/campaigns/new' : '/register'} className="btn-primary mt-8 px-6 py-3 text-base">Create your first campaign</Link>
        <p className="mt-3 text-xs text-slate-500">AI output is a draft. Review every claim before you publish.</p>
      </section>
      <section className="mx-auto grid max-w-6xl gap-4 px-4 pb-16 md:grid-cols-3">
        {FEATURES.map(([t, d]) => (<div key={t} className="card"><h3 className="font-semibold">{t}</h3><p className="mt-1 text-sm text-slate-600">{d}</p></div>))}
      </section>
    </div>
  )
}
