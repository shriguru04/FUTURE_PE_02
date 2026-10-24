import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { EmptyState, ErrorBox, Field, PageHeader, Spinner } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { useMeta } from '../hooks/useMeta'
import { api, errorMessage } from '../services/api'
import { Brand, Campaign, Page, Product } from '../services/types'

interface V { brand_id: string; product_id: string; name: string; objective: string; platform: string; notes: string }

export default function CampaignWizard() {
  const nav = useNavigate()
  const toast = useToast()
  const meta = useMeta()
  const [step, setStep] = useState(1)
  const { register, handleSubmit, watch, trigger, formState: { errors, isSubmitting } } = useForm<V>({ defaultValues: { platform: 'instagram_reels' } })
  const brands = useFetch(async () => (await api.get<Page<Brand>>('/brands', { params: { page_size: 100 } })).data.items, [])
  const brandId = watch('brand_id')
  const products = useFetch(async () => (brandId ? (await api.get<Page<Product>>('/products', { params: { brand_id: brandId, page_size: 100 } })).data.items : []), [brandId])

  if (brands.loading) return <Spinner />
  if (brands.error) return <ErrorBox message={brands.error} onRetry={brands.reload} />
  if (!brands.data?.length) return <EmptyState title="Create a brand first" text="Campaigns are built from a brand (and ideally a product with verified claims)." to="/app/brands" cta="Create a brand" />

  const next = async (fields: (keyof V)[]) => { if (await trigger(fields)) setStep(step + 1) }
  const onSubmit = async (v: V) => {
    try {
      const { data } = await api.post<Campaign>('/campaigns', { ...v, product_id: v.product_id || null })
      toast.success('Campaign created. Now generate content.')
      nav(`/app/campaigns/${data.id}/generate`)
    } catch (e) { toast.error(errorMessage(e)) }
  }

  return (
    <div className="max-w-2xl">
      <PageHeader title="New campaign" subtitle={`Step ${step} of 3`} />
      <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4" noValidate>
        <div className={step === 1 ? 'space-y-4' : 'hidden'}>
          <Field label="Brand *" htmlFor="brand_id" error={errors.brand_id?.message}>
            <select id="brand_id" className="input" {...register('brand_id', { required: 'Choose a brand.' })}>
              <option value="">Select a brand…</option>{brands.data.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}</select></Field>
          <Field label="Product" htmlFor="product_id" help="Strongly recommended: the AI only uses claims you list on the product.">
            <select id="product_id" className="input" {...register('product_id')}>
              <option value="">No product</option>{products.data?.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
          {!products.loading && brandId && products.data?.length === 0 && <p className="text-xs text-amber-700">This brand has no products. <Link className="underline" to="/app/products">Add one</Link>.</p>}
          <button type="button" className="btn-primary" onClick={() => next(['brand_id'])}>Next</button>
        </div>
        <div className={step === 2 ? 'space-y-4' : 'hidden'}>
          <Field label="Campaign name *" htmlFor="name" error={errors.name?.message}>
            <input id="name" className="input" {...register('name', { required: 'Name is required.', maxLength: { value: 200, message: 'Max 200 characters.' } })} /></Field>
          <Field label="Marketing objective" htmlFor="objective" help="e.g. drive first purchases, grow awareness of the new flavour">
            <textarea id="objective" rows={3} className="input" {...register('objective', { maxLength: 4000 })} /></Field>
          <div className="flex gap-2"><button type="button" className="btn-secondary" onClick={() => setStep(1)}>Back</button>
            <button type="button" className="btn-primary" onClick={() => next(['name'])}>Next</button></div>
        </div>
        <div className={step === 3 ? 'space-y-4' : 'hidden'}>
          <Field label="Target platform *" htmlFor="platform">
            <select id="platform" className="input" {...register('platform', { required: true })}>
              {meta.data && Object.entries(meta.data.platforms).map(([k, p]) => <option key={k} value={k}>{p.label}</option>)}</select></Field>
          <Field label="Notes" htmlFor="notes"><textarea id="notes" rows={2} className="input" {...register('notes', { maxLength: 4000 })} /></Field>
          <div className="flex gap-2"><button type="button" className="btn-secondary" onClick={() => setStep(2)}>Back</button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>{isSubmitting ? 'Creating…' : 'Create campaign'}</button></div>
        </div>
      </form>
    </div>
  )
}
