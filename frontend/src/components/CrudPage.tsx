import { ReactNode, useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { api, errorMessage } from '../services/api'
import { Brand, Page } from '../services/types'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { linesToText, parseLines } from '../utils/format'
import { ConfirmDialog } from './ConfirmDialog'
import { EmptyState, ErrorBox, Field, PageHeader, Spinner } from './ui'

export interface FieldDef {
  name: string
  label: string
  type: 'text' | 'textarea' | 'lines' | 'number' | 'url' | 'brand'
  required?: boolean
  maxLength?: number
  help?: string
  createOnly?: boolean
}

interface Props<T extends { id: string }> {
  title: string
  singular: string
  subtitle: string
  endpoint: string
  fields: FieldDef[]
  summary: (item: T) => ReactNode
  emptyText: string
}

type Values = Record<string, string>

export function CrudPage<T extends { id: string; name: string }>({ title, singular, subtitle, endpoint, fields, summary, emptyText }: Props<T>) {
  const toast = useToast()
  const [q, setQ] = useState('')
  const [editing, setEditing] = useState<T | 'new' | null>(null)
  const [deleting, setDeleting] = useState<T | null>(null)
  const [busy, setBusy] = useState(false)
  const list = useFetch(async () => (await api.get<Page<T>>(`/${endpoint}`, { params: { q: q || undefined, page_size: 100 } })).data, [endpoint, q])
  const needsBrands = fields.some((f) => f.type === 'brand')
  const brands = useFetch(async () => (needsBrands ? (await api.get<Page<Brand>>('/brands', { params: { page_size: 100 } })).data.items : []), [needsBrands])

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<Values>()

  useEffect(() => {
    if (editing === null) return
    const v: Values = {}
    for (const f of fields) {
      const raw = editing === 'new' ? undefined : (editing as any)[f.name]
      v[f.name] = f.type === 'lines' ? linesToText(raw) : raw === null || raw === undefined ? (f.name === 'language' ? 'English' : '') : String(raw)
    }
    reset(v)
  }, [editing, fields, reset])

  const onSubmit = async (values: Values) => {
    const body: Record<string, unknown> = {}
    for (const f of fields) {
      if (editing !== 'new' && f.createOnly) continue
      const v = values[f.name] ?? ''
      body[f.name] = f.type === 'lines' ? parseLines(v) : f.type === 'number' ? (v === '' ? null : Number(v)) : v
    }
    try {
      if (editing === 'new') await api.post(`/${endpoint}`, body)
      else await api.patch(`/${endpoint}/${(editing as T).id}`, body)
      toast.success(`${singular} saved.`)
      setEditing(null)
      void list.reload()
    } catch (e) { toast.error(errorMessage(e)) }
  }

  const remove = async () => {
    if (!deleting) return
    setBusy(true)
    try {
      await api.delete(`/${endpoint}/${deleting.id}`)
      toast.success(`${singular} deleted.`)
      setDeleting(null)
      void list.reload()
    } catch (e) { toast.error(errorMessage(e)); setDeleting(null) } finally { setBusy(false) }
  }

  const noBrands = needsBrands && !brands.loading && (brands.data ?? []).length === 0

  return (
    <div>
      <PageHeader title={title} subtitle={subtitle}
        actions={<button className="btn-primary" disabled={noBrands} onClick={() => setEditing('new')}>Add {singular.toLowerCase()}</button>} />
      {noBrands && <EmptyState title="Create a brand first" text="Products belong to a brand." to="/app/brands" cta="Go to brands" />}
      <input className="input mb-4 max-w-sm" placeholder={`Search ${title.toLowerCase()}…`} aria-label={`Search ${title}`} value={q} onChange={(e) => setQ(e.target.value)} />
      {list.loading && <Spinner />}
      {list.error && <ErrorBox message={list.error} onRetry={list.reload} />}
      {!list.loading && !list.error && list.data?.items.length === 0 && !noBrands && <EmptyState title={`No ${title.toLowerCase()} yet`} text={emptyText} />}
      <div className="grid gap-3 md:grid-cols-2">
        {list.data?.items.map((item) => (
          <div key={item.id} className="card">
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-semibold">{item.name}</h3>
              <div className="flex gap-2">
                <button className="btn-secondary btn-sm" onClick={() => setEditing(item)}>Edit</button>
                <button className="btn-secondary btn-sm text-red-600" onClick={() => setDeleting(item)}>Delete</button>
              </div>
            </div>
            <div className="mt-2 text-sm text-slate-600">{summary(item)}</div>
          </div>
        ))}
      </div>

      {editing !== null && (
        <div className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-black/40 p-4" role="dialog" aria-modal="true" aria-label={`${editing === 'new' ? 'Add' : 'Edit'} ${singular}`}>
          <form onSubmit={handleSubmit(onSubmit)} className="my-8 w-full max-w-2xl space-y-4 rounded-xl bg-white p-6 shadow-xl" noValidate>
            <h2 className="text-lg font-semibold">{editing === 'new' ? 'Add' : 'Edit'} {singular.toLowerCase()}</h2>
            {fields.filter((f) => !(editing !== 'new' && f.createOnly)).map((f) => {
              const err = errors[f.name]?.message as string | undefined
              const common = {
                id: `f-${f.name}`, className: 'input',
                ...register(f.name, {
                  required: f.required ? `${f.label} is required.` : false,
                  maxLength: f.maxLength ? { value: f.maxLength, message: `Max ${f.maxLength} characters.` } : undefined,
                  validate: (v) => {
                    if (f.type === 'url' && v && !/^https?:\/\//.test(v)) return 'Must start with http:// or https://'
                    if (f.type === 'number' && v !== '' && (Number.isNaN(Number(v)) || Number(v) < 0)) return 'Enter a number ≥ 0.'
                    return true
                  },
                }),
              }
              return (
                <Field key={f.name} label={f.label + (f.required ? ' *' : '')} htmlFor={`f-${f.name}`} error={err} help={f.help}>
                  {f.type === 'textarea' || f.type === 'lines' ? <textarea rows={3} {...common} />
                    : f.type === 'brand' ? (
                      <select {...common}><option value="">Select a brand…</option>{brands.data?.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}</select>
                    ) : <input type={f.type === 'number' ? 'number' : 'text'} step={f.type === 'number' ? '0.01' : undefined} {...common} />}
                </Field>
              )
            })}
            <div className="flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
              <button type="submit" className="btn-primary" disabled={isSubmitting}>{isSubmitting ? 'Saving…' : 'Save'}</button>
            </div>
          </form>
        </div>
      )}
      <ConfirmDialog open={!!deleting} title={`Delete ${singular.toLowerCase()}?`} busy={busy} onConfirm={remove} onCancel={() => setDeleting(null)}>
        <b>{deleting?.name}</b> will be permanently deleted. This cannot be undone.
      </ConfirmDialog>
    </div>
  )
}
