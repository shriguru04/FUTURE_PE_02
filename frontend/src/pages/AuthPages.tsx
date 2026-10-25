import { ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Field } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { errorMessage } from '../services/api'

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

interface FormValues { email: string; password: string; display_name?: string }

function Shell({ title, children, footer }: { title: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="card w-full max-w-md">
        <Link to="/" className="text-sm font-bold text-brand-700">AdCraft AI</Link>
        <h1 className="mb-4 mt-2 text-2xl font-bold">{title}</h1>
        {children}
        <p className="mt-4 text-center text-sm text-slate-500">{footer}</p>
      </div>
    </div>
  )
}

export function LoginPage() {
  const { login } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  const loc = useLocation() as { state?: { from?: string } }
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>()
  const onSubmit = async (v: FormValues) => {
    try { await login(v.email, v.password); nav(loc.state?.from ?? '/app', { replace: true }) }
    catch (e) { toast.error(errorMessage(e)) }
  }
  return (
    <Shell title="Log in" footer={<>No account? <Link className="text-brand-600 underline" to="/register">Register</Link></>}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <Field label="Email" htmlFor="email" error={errors.email?.message}>
          <input id="email" type="email" autoComplete="email" className="input"
            {...register('email', { required: 'Email is required.', pattern: { value: EMAIL, message: 'Enter a valid email address.' } })} />
        </Field>
        <Field label="Password" htmlFor="password" error={errors.password?.message}>
          <input id="password" type="password" autoComplete="current-password" className="input"
            {...register('password', { required: 'Password is required.' })} />
        </Field>
        <button className="btn-primary w-full" disabled={isSubmitting}>{isSubmitting ? 'Logging in…' : 'Log in'}</button>
      </form>
    </Shell>
  )
}

export function RegisterPage() {
  const { register: signup } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>()
  const onSubmit = async (v: FormValues) => {
    try { await signup(v.email, v.password, v.display_name ?? ''); nav('/app', { replace: true }) }
    catch (e) { toast.error(errorMessage(e)) }
  }
  return (
    <Shell title="Create your account" footer={<>Already registered? <Link className="text-brand-600 underline" to="/login">Log in</Link></>}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <Field label="Name (optional)" htmlFor="display_name"><input id="display_name" className="input" {...register('display_name', { maxLength: 120 })} /></Field>
        <Field label="Email" htmlFor="email" error={errors.email?.message}>
          <input id="email" type="email" autoComplete="email" className="input"
            {...register('email', { required: 'Email is required.', pattern: { value: EMAIL, message: 'Enter a valid email address.' } })} />
        </Field>
        <Field label="Password" htmlFor="password" error={errors.password?.message} help="At least 8 characters.">
          <input id="password" type="password" autoComplete="new-password" className="input"
            {...register('password', { required: 'Password is required.', minLength: { value: 8, message: 'Use at least 8 characters.' }, maxLength: { value: 128, message: 'Too long.' } })} />
        </Field>
        <button className="btn-primary w-full" disabled={isSubmitting}>{isSubmitting ? 'Creating…' : 'Create account'}</button>
      </form>
    </Shell>
  )
}
