import { AlertTriangle, Sparkles, TrendingUp } from 'lucide-react'

import type { ScriptSummary } from '../types'

type Props = {
  projectId: string
  projectName: string
  description?: string | null
  scripts?: ScriptSummary[]
}

type Insight = {
  label: string
  value: string
  tone: 'positive' | 'warning' | 'neutral'
}

function insightsFromKeywords(description?: string | null, scripts?: ScriptSummary[]): Insight[] {
  const source = `${description ?? ''}`.toLowerCase()
  const positives: string[] = []
  const risks: string[] = []

  if (/(twist|mystery|thriller|suspense|secret|betray|revenge|romance|family|crime)/i.test(source)) {
    positives.push('Strong emotional hook')
  }
  if (/(betray|revenge|violence|trauma|death|dark|grief)/i.test(source)) {
    risks.push('High emotional intensity')
  }
  if (/(young|college|school|student|teen|friend|family)/i.test(source)) {
    positives.push('Relatable everyday stakes')
  }
  if (/(love|romance|heartbreak|relationship|friendship)/i.test(source)) {
    positives.push('Relationship-driven retention')
  }
  if (/(comedy|funny|satire|light|warm)/i.test(source)) {
    positives.push('Easy binge appeal')
  }
  if (/(politics|social|history|war|religion|taboo)/i.test(source)) {
    risks.push('Potential sensitivity risk')
  }
  if (/(murder|crime|illegal|drug|abuse)/i.test(source)) {
    risks.push('Content moderation attention')
  }

  const insights: Insight[] = []
  if (positives.length) {
    insights.push({ label: 'Potential benefits', value: positives.slice(0, 3).join(' • '), tone: 'positive' })
  }
  if (risks.length) {
    insights.push({ label: 'Potential risks', value: risks.slice(0, 3).join(' • '), tone: 'warning' })
  }

  if (!insights.length) {
    insights.push({ label: 'Signal', value: 'The concept is broad enough to generate a strong hook.', tone: 'neutral' })
    insights.push({ label: 'Sample trend', value: 'High curiosity factor • Strong character-driven momentum', tone: 'positive' })
    insights.push({ label: 'Watchout', value: 'Some emotional beats may need pacing support', tone: 'warning' })
  }

  if ((scripts?.length ?? 0) > 0) {
    insights.push({
      label: 'Draft momentum',
      value: `${scripts?.length ?? 0} draft${(scripts?.length ?? 0) === 1 ? '' : 's'} ready to build on.`,
      tone: 'positive',
    })
  }

  return insights
}

function scoreFromScripts(scripts?: ScriptSummary[]) {
  const count = scripts?.length ?? 0
  if (count >= 3) return 78
  if (count >= 1) return 64
  return 58
}

export function ProjectAnalyticsPanel({ projectId: _projectId, projectName, description, scripts }: Props) {
  const insights = insightsFromKeywords(description, scripts)
  const score = scoreFromScripts(scripts)

  return (
    <section className="overflow-hidden rounded-[20px] border border-stone-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-stone-200 bg-stone-50 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-stone-500">
            <Sparkles className="h-3.5 w-3.5 text-[#e6194d]" />
            Audience signal
          </div>
          <h3 className="mt-2 text-[16px] font-semibold text-stone-900">
            {projectName} is primed for a strong audience response when the hook is clear.
          </h3>
          <p className="mt-1 text-[12px] leading-5 text-stone-500">
            Signals derived from project description and draft activity.
          </p>
        </div>

        <div className="rounded-[12px] border border-stone-200 bg-stone-50 px-3 py-2 text-right">
          <p className="text-[10px] uppercase tracking-[0.24em] text-stone-500">Estimated appeal</p>
          <p className="mt-1 text-[22px] font-bold text-stone-900">{score}<span className="text-[14px] font-medium text-stone-400">/100</span></p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {insights.map((item) => (
          <div key={item.label} className="rounded-[14px] border border-stone-200 bg-stone-50 p-3">
            <div className="flex items-center gap-2">
              {item.tone === 'warning' ? (
                <AlertTriangle className="h-4 w-4 text-amber-500" />
              ) : item.tone === 'positive' ? (
                <TrendingUp className="h-4 w-4 text-emerald-500" />
              ) : (
                <Sparkles className="h-4 w-4 text-[#e6194d]" />
              )}
              <p className="text-[12px] font-semibold text-stone-800">{item.label}</p>
            </div>
            <p className="mt-2 text-[12px] leading-5 text-stone-600">{item.value}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
