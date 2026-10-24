import { CrudPage, FieldDef } from '../components/CrudPage'
import { Product } from '../services/types'
import { fmtMoney } from '../utils/format'

const FIELDS: FieldDef[] = [
  { name: 'brand_id', label: 'Brand', type: 'brand', required: true, createOnly: true },
  { name: 'name', label: 'Product name', type: 'text', required: true, maxLength: 200 },
  { name: 'description', label: 'Description', type: 'textarea', maxLength: 4000 },
  { name: 'features', label: 'Features', type: 'lines', help: 'One per line.' },
  { name: 'benefits', label: 'Benefits', type: 'lines', help: 'One per line.' },
  { name: 'price', label: 'Price (optional)', type: 'number' },
  { name: 'intended_audience', label: 'Intended audience', type: 'textarea', maxLength: 4000 },
  { name: 'supported_claims', label: 'Supported product claims', type: 'lines', help: 'Only claims you can prove. The AI may only mark these as "supported". One per line.' },
  { name: 'limitations', label: 'Known limitations', type: 'textarea', maxLength: 4000 },
  { name: 'offer_details', label: 'Offer details', type: 'textarea', maxLength: 4000 },
  { name: 'cta', label: 'Product CTA', type: 'text', maxLength: 300 },
]

export default function ProductsPage() {
  return (
    <CrudPage<Product> title="Products" singular="Product" endpoint="products" fields={FIELDS}
      subtitle="Verified facts and claims the AI is allowed to use."
      emptyText="Add a product to give the AI real facts to work with."
      summary={(p) => <>{p.price !== null ? fmtMoney(p.price) + ' · ' : ''}{p.supported_claims.length} supported claim(s) · {p.features.length} feature(s)</>} />
  )
}
