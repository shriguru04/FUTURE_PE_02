import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from 'react'
import { api } from '../services/api'
import { User } from '../services/types'

interface Ctx {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName: string) => Promise<void>
  logout: () => Promise<void>
  setUser: (u: User | null) => void
}

const AuthCtx = createContext<Ctx | null>(null)

export function useAuth(): Ctx {
  const c = useContext(AuthCtx)
  if (!c) throw new Error('useAuth must be used inside AuthProvider')
  return c
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<User>('/auth/me').then((r) => setUser(r.data)).catch(() => setUser(null)).finally(() => setLoading(false))
    const expired = () => setUser(null)
    window.addEventListener('auth:expired', expired)
    return () => window.removeEventListener('auth:expired', expired)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setUser((await api.post<User>('/auth/login', { email, password })).data)
  }, [])
  const register = useCallback(async (email: string, password: string, display_name: string) => {
    setUser((await api.post<User>('/auth/register', { email, password, display_name })).data)
  }, [])
  const logout = useCallback(async () => {
    try { await api.post('/auth/logout') } finally { setUser(null) }
  }, [])

  return <AuthCtx.Provider value={{ user, loading, login, register, logout, setUser }}>{children}</AuthCtx.Provider>
}
