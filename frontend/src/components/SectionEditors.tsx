import { linesToText, parseLines } from '../utils/format'

type P = any
interface Props { value: P; onChange: (v: P) => void }

const num = (s: string) => { const n = parseInt(s, 10); return Number.isNaN(n) ? 0 : n }

export function ScriptEditor({ value, onChange }: Props) {
  const set = (patch: P) => onChange({ ...value, ...patch })
  const setScene = (i: number, patch: P) => set({ scenes: value.scenes.map((s: P, j: number) => (j === i ? { ...s, ...patch } : s)) })
  const addScene = () => set({ scenes: [...value.scenes, { scene_number: value.scenes.length + 1, duration_seconds: 5, visual_direction: 'New scene', dialogue: '', on_screen_text: '', transition: '', audio_direction: '' }] })
  const removeScene = (i: number) => set({ scenes: value.scenes.filter((_: P, j: number) => j !== i).map((s: P, j: number) => ({ ...s, scene_number: j + 1 })) })
  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-3">
        <label className="sm:col-span-2 text-sm">Title<input className="input mt-1" value={value.title} onChange={(e) => set({ title: e.target.value })} /></label>
        <label className="text-sm">Total seconds<input type="number" className="input mt-1" value={value.total_duration_seconds} onChange={(e) => set({ total_duration_seconds: num(e.target.value) })} /></label>
      </div>
      {value.scenes.map((s: P, i: number) => (
        <fieldset key={i} className="rounded-lg border border-slate-200 p-3">
          <legend className="px-1 text-xs font-semibold text-slate-500">Scene {s.scene_number}</legend>
          <div className="grid gap-2 sm:grid-cols-2">
            <label className="text-xs">Duration (s)<input type="number" className="input mt-1" value={s.duration_seconds} onChange={(e) => setScene(i, { duration_seconds: num(e.target.value) })} /></label>
            <label className="text-xs">Transition<input className="input mt-1" value={s.transition} onChange={(e) => setScene(i, { transition: e.target.value })} /></label>
            <label className="text-xs sm:col-span-2">Visual direction<textarea rows={2} className="input mt-1" value={s.visual_direction} onChange={(e) => setScene(i, { visual_direction: e.target.value })} /></label>
            <label className="text-xs sm:col-span-2">Spoken dialogue<textarea rows={2} className="input mt-1" value={s.dialogue} onChange={(e) => setScene(i, { dialogue: e.target.value })} /></label>
            <label className="text-xs">On-screen text<input className="input mt-1" value={s.on_screen_text} onChange={(e) => setScene(i, { on_screen_text: e.target.value })} /></label>
            <label className="text-xs">Audio / music<input className="input mt-1" value={s.audio_direction} onChange={(e) => setScene(i, { audio_direction: e.target.value })} /></label>
          </div>
          {value.scenes.length > 1 && <button type="button" className="mt-2 text-xs text-red-600 underline" onClick={() => removeScene(i)}>Remove scene</button>}
        </fieldset>
      ))}
      <button type="button" className="btn-secondary btn-sm" onClick={addScene}>Add scene</button>
      <label className="block text-sm">Voice-over script<textarea rows={3} className="input mt-1" value={value.voice_over} onChange={(e) => set({ voice_over: e.target.value })} /></label>
    </div>
  )
}

export function SectionEditor({ section, value, onChange }: { section: string } & Props) {
  switch (section) {
    case 'summary':
    case 'caption':
      return <textarea aria-label={section} rows={4} className="input" value={value.text} onChange={(e) => onChange({ text: e.target.value })} />
    case 'hooks':
    case 'hashtags':
    case 'variations':
      return <textarea aria-label={section} rows={Math.min(10, Math.max(4, value.items.length + 1))} className="input" value={linesToText(value.items)}
        onChange={(e) => onChange({ items: parseLines(e.target.value) })} />
    case 'ctas':
      return (
        <div className="space-y-2">
          <label className="block text-sm">Primary CTA<input className="input mt-1" value={value.primary} onChange={(e) => onChange({ ...value, primary: e.target.value })} /></label>
          <label className="block text-sm">Alternatives (one per line)<textarea rows={3} className="input mt-1" value={linesToText(value.alternatives)} onChange={(e) => onChange({ ...value, alternatives: parseLines(e.target.value) })} /></label>
        </div>)
    case 'primary_script':
      return <ScriptEditor value={value} onChange={onChange} />
    case 'alt_scripts':
      return (
        <div className="space-y-4">
          {value.items.map((s: P, i: number) => (
            <div key={i} className="rounded-lg border border-slate-200 p-3">
              <ScriptEditor value={s} onChange={(v) => onChange({ items: value.items.map((x: P, j: number) => (j === i ? v : x)) })} />
              <button type="button" className="mt-2 text-xs text-red-600 underline" onClick={() => onChange({ items: value.items.filter((_: P, j: number) => j !== i) })}>Remove this script</button>
            </div>))}
          {value.items.length === 0 && <p className="text-sm text-slate-500">No alternative scripts. Use Regenerate to create some.</p>}
        </div>)
    case 'adaptation':
      return (
        <div className="grid gap-2 sm:grid-cols-2">
         
{Object.entries(value ?? {}).map(([k, v]) => (
  <label key={k} className="text-xs">
    {k.replace(/_/g, ' ')}
    <input
      className="input mt-1"
      type={typeof v === 'number' ? 'number' : 'text'}
      value={v ?? ''}
      onChange={(e) =>
        onChange({
          ...(value ?? {}),
          [k]:
            typeof v === 'number'
              ? num(e.target.value)
              : e.target.value,
        })
      }
    />
  </label>
))}

        </div>)
    case 'claims_review':
      return (
        <div className="space-y-2">
          <p className="text-xs text-slate-500">Review every claim against real evidence before publishing.</p>
          {value.items.map((c: P, i: number) => (
            <div key={i} className="grid gap-2 rounded-lg border border-slate-200 p-2 sm:grid-cols-6">
              <input aria-label="Claim" className="input sm:col-span-3" value={c.claim} onChange={(e) => onChange({ items: value.items.map((x: P, j: number) => (j === i ? { ...x, claim: e.target.value } : x)) })} />
              <select aria-label="Status" className="input sm:col-span-1" value={c.status} onChange={(e) => onChange({ items: value.items.map((x: P, j: number) => (j === i ? { ...x, status: e.target.value } : x)) })}>
                <option value="supported">supported</option><option value="needs_verification">needs verification</option><option value="unsupported">unsupported</option></select>
              <input aria-label="Note" className="input sm:col-span-2" value={c.note} onChange={(e) => onChange({ items: value.items.map((x: P, j: number) => (j === i ? { ...x, note: e.target.value } : x)) })} />
            </div>))}
        </div>)
    default:
      return <pre className="text-xs">{JSON.stringify(value, null, 2)}</pre>
  }
}
