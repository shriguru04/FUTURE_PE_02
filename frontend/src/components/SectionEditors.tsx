import { linesToText, parseLines } from '../utils/format'

type P = any
interface Props { value: P; onChange: (v: P) => void }

const num = (s: string) => {
  const n = parseInt(s, 10)
  return Number.isNaN(n) ? 0 : n
}
const asObject = (v: P): Record<string, any> =>
  v !== null && typeof v === 'object' && !Array.isArray(v) ? v : {}
const asArray = (v: P): any[] => Array.isArray(v) ? v : []
const asText = (v: P): string => v == null ? '' : String(v)

export function ScriptEditor({ value, onChange }: Props) {
  const data = asObject(value)
  const scenes = asArray(data.scenes)
  const set = (patch: P) => onChange({ ...data, ...patch })
  const setScene = (i: number, patch: P) =>
    set({ scenes: scenes.map((s: P, j: number) => j === i ? { ...asObject(s), ...patch } : s) })
  const addScene = () => set({ scenes: [...scenes, {
    scene_number: scenes.length + 1, duration_seconds: 5, visual_direction: 'New scene',
    dialogue: '', on_screen_text: '', transition: '', audio_direction: '',
  }] })
  const removeScene = (i: number) =>
    set({ scenes: scenes.filter((_: P, j: number) => j !== i).map((s: P, j: number) => ({ ...asObject(s), scene_number: j + 1 })) })

  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-3">
        <label className="sm:col-span-2 text-sm">Title
          <input className="input mt-1" value={asText(data.title)} onChange={(e) => set({ title: e.target.value })} />
        </label>
        <label className="text-sm">Total seconds
          <input type="number" className="input mt-1" value={data.total_duration_seconds ?? 0} onChange={(e) => set({ total_duration_seconds: num(e.target.value) })} />
        </label>
      </div>
      {scenes.map((raw: P, i: number) => {
        const s = asObject(raw)
        return (
          <fieldset key={i} className="rounded-lg border border-slate-200 p-3">
            <legend className="px-1 text-xs font-semibold text-slate-500">Scene {s.scene_number ?? i + 1}</legend>
            <div className="grid gap-2 sm:grid-cols-2">
              <label className="text-xs">Duration (s)<input type="number" className="input mt-1" value={s.duration_seconds ?? 0} onChange={(e) => setScene(i, { duration_seconds: num(e.target.value) })} /></label>
              <label className="text-xs">Transition<input className="input mt-1" value={asText(s.transition)} onChange={(e) => setScene(i, { transition: e.target.value })} /></label>
              <label className="text-xs sm:col-span-2">Visual direction<textarea rows={2} className="input mt-1" value={asText(s.visual_direction)} onChange={(e) => setScene(i, { visual_direction: e.target.value })} /></label>
              <label className="text-xs sm:col-span-2">Spoken dialogue<textarea rows={2} className="input mt-1" value={asText(s.dialogue)} onChange={(e) => setScene(i, { dialogue: e.target.value })} /></label>
              <label className="text-xs">On-screen text<input className="input mt-1" value={asText(s.on_screen_text)} onChange={(e) => setScene(i, { on_screen_text: e.target.value })} /></label>
              <label className="text-xs">Audio / music<input className="input mt-1" value={asText(s.audio_direction)} onChange={(e) => setScene(i, { audio_direction: e.target.value })} /></label>
            </div>
            {scenes.length > 1 && <button type="button" className="mt-2 text-xs text-red-600 underline" onClick={() => removeScene(i)}>Remove scene</button>}
          </fieldset>
        )
      })}
      <button type="button" className="btn-secondary btn-sm" onClick={addScene}>Add scene</button>
      <label className="block text-sm">Voice-over script<textarea rows={3} className="input mt-1" value={asText(data.voice_over)} onChange={(e) => set({ voice_over: e.target.value })} /></label>
    </div>
  )
}

export function SectionEditor({ section, value, onChange }: { section: string } & Props) {
  const data = asObject(value)
  switch (section) {
    case 'summary':
    case 'caption':
      return <textarea aria-label={section} rows={4} className="input" value={asText(data.text)} onChange={(e) => onChange({ ...data, text: e.target.value })} />
    case 'hooks':
    case 'hashtags':
    case 'variations': {
      const items = asArray(data.items)
      return <textarea aria-label={section} rows={Math.min(10, Math.max(4, items.length + 1))} className="input" value={linesToText(items)}
        onChange={(e) => onChange({ ...data, items: parseLines(e.target.value) })} />
    }
    case 'ctas':
      return <div className="space-y-2">
        <label className="block text-sm">Primary CTA<input className="input mt-1" value={asText(data.primary)} onChange={(e) => onChange({ ...data, primary: e.target.value })} /></label>
        <label className="block text-sm">Alternatives (one per line)<textarea rows={3} className="input mt-1" value={linesToText(asArray(data.alternatives))} onChange={(e) => onChange({ ...data, alternatives: parseLines(e.target.value) })} /></label>
      </div>
    case 'primary_script':
      return <ScriptEditor value={data} onChange={onChange} />
    case 'alt_scripts': {
      const items = asArray(data.items)
      return <div className="space-y-4">
        {items.map((s: P, i: number) => <div key={i} className="rounded-lg border border-slate-200 p-3">
          <ScriptEditor value={asObject(s)} onChange={(v) => onChange({ ...data, items: items.map((x: P, j: number) => j === i ? v : x) })} />
          <button type="button" className="mt-2 text-xs text-red-600 underline" onClick={() => onChange({ ...data, items: items.filter((_: P, j: number) => j !== i) })}>Remove this script</button>
        </div>)}
        {items.length === 0 && <p className="text-sm text-slate-500">No alternative scripts. Use Regenerate to create some.</p>}
      </div>
    }
    case 'adaptation':
      return <div className="grid gap-2 sm:grid-cols-2">
        {Object.entries(data).map(([k, v]) => <label key={k} className="text-xs">{k.replace(/_/g, ' ')}
          <input className="input mt-1" type={typeof v === 'number' ? 'number' : 'text'} value={asText(v)}
            onChange={(e) => onChange({ ...data, [k]: typeof v === 'number' ? num(e.target.value) : e.target.value })} />
        </label>)}
      </div>
    case 'claims_review': {
      const items = asArray(data.items)
      return <div className="space-y-2">
        <p className="text-xs text-slate-500">Review every claim against real evidence before publishing.</p>
        {items.map((raw: P, i: number) => {
          const c = asObject(raw)
          const update = (patch: P) => onChange({ ...data, items: items.map((x: P, j: number) => j === i ? { ...asObject(x), ...patch } : x) })
          return <div key={i} className="grid gap-2 rounded-lg border border-slate-200 p-2 sm:grid-cols-6">
            <input aria-label="Claim" className="input sm:col-span-3" value={asText(c.claim)} onChange={(e) => update({ claim: e.target.value })} />
            <select aria-label="Status" className="input sm:col-span-1" value={c.status ?? 'needs_verification'} onChange={(e) => update({ status: e.target.value })}>
              <option value="supported">supported</option><option value="needs_verification">needs verification</option><option value="unsupported">unsupported</option>
            </select>
            <input aria-label="Note" className="input sm:col-span-2" value={asText(c.note)} onChange={(e) => update({ note: e.target.value })} />
          </div>
        })}
      </div>
    }
    default:
      return <pre className="text-xs">{JSON.stringify(data, null, 2)}</pre>
  }
}
