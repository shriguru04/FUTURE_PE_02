import { CrudPage, FieldDef } from '../components/CrudPage'
import { Brand } from '../services/types'

const FIELDS: FieldDef[] = [
  { name: 'name', label: 'Brand name', type: 'text', required: true, maxLength: 200 },
  { name: 'category', label: 'Business category', type: 'text', maxLength: 300 },
  { name: 'description', label: 'Business description', type: 'textarea', maxLength: 4000 },
  { name: 'target_audience', label: 'Target audience', type: 'textarea', maxLength: 4000 },
  { name: 'voice', label: 'Brand voice', type: 'text', maxLength: 300, help: 'e.g. warm, witty, expert' },
  { name: 'language', label: 'Preferred language', type: 'text', maxLength: 300 },
  { name: 'writing_style', label: 'Writing style', type: 'text', maxLength: 300 },
  { name: 'messaging_guidelines', label: 'Messaging guidelines', type: 'textarea', maxLength: 4000 },
  { name: 'avoid_terms', label: 'Words or claims to avoid', type: 'lines', help: 'One per line. Flagged in the claims review if they appear.' },
  { name: 'website_url', label: 'Website URL', type: 'url', maxLength: 300 },
  { name: 'default_cta', label: 'Default CTA', type: 'text', maxLength: 300 },
]

export default function BrandsPage() {
  return (
    <CrudPage<Brand> title="Brands" singular="Brand" endpoint="brands" fields={FIELDS}
      subtitle="Voice, audience and guardrails the AI must respect."
      emptyText="Add your first brand to start creating campaigns."
      summary={(b) => <>{b.category || 'No category'} · {b.voice || 'No voice set'}{(Array.isArray(b.avoid_terms) ? b.avoid_terms.length : 0) > 0 && ` · avoids ${b.avoid_terms.length} term(s)`}</>} />
  )
}
