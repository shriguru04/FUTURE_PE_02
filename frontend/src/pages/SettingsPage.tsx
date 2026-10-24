import { useForm } from 'react-hook-form'
import { Field, PageHeader, Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useMeta } from '../hooks/useMeta'
import { api, errorMessage } from '../services/api'
import { User } from '../services/types'

export default function SettingsPage() {
  const { user, setUser } = useAuth()
  const toast = useToast()
  const meta = useMeta()
  const profile = useForm<{ display_name: string }>({ defaultValues: { display_name: user?.display_name ?? '' } })
  const pw = useForm<{ current_password: string; new_password: string; confirm: string }>()

  return (
    <div className="max-w-2xl">
      <PageHeader title="Settings" />
      <form className="card mb-4 space-y-4" noValidate onSubmit={profile.handleSubmit(async (v) => {
        try { setUser((await api.patch<User>('/auth/me', v)).data); toast.success('Profile updated.') } catch (e) { toast.error(errorMessage(e)) } })}>
        <h2 className="font-semibold">Profile</h2>
        <Field label="Email" htmlFor="email"><input id="email" className="input bg-slate-100" value={user?.email ?? ''} readOnly /></Field>
        <Field label="Display name" htmlFor="display_name" error={profile.formState.errors.display_name?.message}>
          <input id="display_name" className="input" {...profile.register('display_name', { maxLength: { value: 120, message: 'Max 120 characters.' } })} /></Field>
        <button className="btn-primary">Save profile</button>
      </form>

      <form className="card mb-4 space-y-4" noValidate onSubmit={pw.handleSubmit(async (v) => {
        try { await api.post('/auth/change-password', { current_password: v.current_password, new_password: v.new_password }); toast.success('Password changed.'); pw.reset() }
        catch (e) { toast.error(errorMessage(e)) } })}>
        <h2 className="font-semibold">Change password</h2>
        <Field label="Current password" htmlFor="cur" error={pw.formState.errors.current_password?.message}><input id="cur" type="password" autoComplete="current-password" className="input" {...pw.register('current_password', { required: 'Required.' })} /></Field>
        <Field label="New password" htmlFor="new" error={pw.formState.errors.new_password?.message}><input id="new" type="password" autoComplete="new-password" className="input" {...pw.register('new_password', { required: 'Required.', minLength: { value: 8, message: 'Use at least 8 characters.' } })} /></Field>
        <Field label="Confirm new password" htmlFor="conf" error={pw.formState.errors.confirm?.message}><input id="conf" type="password" autoComplete="new-password" className="input"
          {...pw.register('confirm', { validate: (v) => v === pw.getValues('new_password') || 'Passwords do not match.' })} /></Field>
        <button className="btn-primary">Change password</button>
      </form>

      <section className="card"><h2 className="mb-2 font-semibold">AI provider</h2>
        {meta.loading ? <Spinner /> : meta.data && (
          <dl className="grid grid-cols-3 gap-y-1 text-sm">
            <dt className="text-slate-500">Status</dt><dd className="col-span-2">{meta.data.llm.configured ? (meta.data.llm.is_mock ? 'Mock (development only)' : 'Configured') : 'Not configured'}</dd>
            <dt className="text-slate-500">Model</dt><dd className="col-span-2">{meta.data.llm.model}</dd>
          </dl>)}
        <p className="mt-2 text-xs text-slate-500">The provider and API key are set by the server administrator via environment variables and are never exposed to the browser.</p>
      </section>
    </div>
  )
}
