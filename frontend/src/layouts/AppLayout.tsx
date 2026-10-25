import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV = [
  ['/app', 'Dashboard', true], ['/app/campaigns', 'Campaigns', false], ['/app/campaigns/new', 'New campaign', true],
  ['/app/brands', 'Brands', false], ['/app/products', 'Products', false],
  ['/app/analytics', 'Analytics', false], ['/app/settings', 'Settings', false],
] as const

export function AppLayout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  return (
    <div className="min-h-screen md:flex">
      <header className="flex items-center justify-between bg-brand-900 px-4 py-3 text-white md:hidden">
        <span className="font-bold">AdCraft AI</span>
        <button className="rounded p-2 hover:bg-brand-700" aria-label="Toggle menu" aria-expanded={open} onClick={() => setOpen(!open)}>☰</button>
      </header>
      <aside className={`${open ? 'block' : 'hidden'} w-full shrink-0 bg-brand-900 p-4 text-white md:block md:min-h-screen md:w-60`}>
        <div className="mb-6 hidden text-xl font-bold md:block">AdCraft AI</div>
        <nav className="space-y-1" aria-label="Main">
          {NAV.map(([to, label, end]) => (
            <NavLink key={to} to={to} end={end} onClick={() => setOpen(false)}
              className={({ isActive }) => `block rounded-lg px-3 py-2 text-sm ${isActive ? 'bg-brand-700 font-medium' : 'text-indigo-100 hover:bg-brand-700/60'}`}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-8 border-t border-white/20 pt-4 text-xs text-indigo-200">
          <div className="truncate">{user?.display_name || user?.email}</div>
          <button className="mt-2 underline" onClick={async () => { await logout(); nav('/') }}>Log out</button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 p-4 md:p-8"><Outlet /></main>
    </div>
  )
}
