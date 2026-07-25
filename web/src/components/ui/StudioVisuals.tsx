import heroIllustration from '@/assets/ai-story-hero.svg'
import ecosystemIllustration from '@/assets/ai-story-ecosystem.svg'
import visualsIllustration from '@/assets/ai-story-visuals.svg'

const visuals = [
  {
    src: heroIllustration,
    title: 'Prompt to premiere',
    description: 'Turn a seed idea into a launch-ready script flow.',
  },
  {
    src: visualsIllustration,
    title: 'Visuals in sync',
    description: 'Shape scenes, beats, and imagery around the story.',
  },
  {
    src: ecosystemIllustration,
    title: 'Studio-ready output',
    description: 'Package voice, context, and draft assets together.',
  },
] as const

export function StudioVisuals() {
  return (
    <div className="grid gap-3 md:grid-cols-3">
      {visuals.map((visual) => (
        <div
          key={visual.title}
          className="overflow-hidden rounded-[14px] border border-[var(--folio-border)] bg-[var(--surface-1)]"
        >
          <img
            src={visual.src}
            alt={visual.title}
            className="h-36 w-full object-cover"
          />
          <div className="p-3">
            <p className="text-[12px] font-semibold text-[var(--text-primary)]">{visual.title}</p>
            <p className="mt-1 text-[11px] leading-5 text-[var(--text-secondary)]">
              {visual.description}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
