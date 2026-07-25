import { Info, Settings2, User, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTheme } from 'next-themes'

import { BrandMark } from '@/components/brand/BrandMark'
import { cn } from '@/lib/utils'

type Section = 'profile' | 'preferences' | 'about'

type Props = {
  open: boolean
  onClose: () => void
}

export function SettingsSheet({ open, onClose }: Props) {
  const [section, setSection] = useState<Section>('profile')
  const { theme, setTheme } = useTheme()

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[80] flex justify-end">
      <button
        type="button"
        aria-label="Close settings"
        className="settings-backdrop absolute inset-0 overlay-backdrop"
        onClick={onClose}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
        className="settings-panel relative z-10 flex h-full w-full max-w-[420px] flex-col border-l border-[var(--folio-border)] bg-[var(--surface-2)] shadow-[-24px_0_60px_rgba(0,0,0,0.18)]"
      >
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-[var(--folio-border)] px-5">
          <div className="flex items-center gap-2.5">
            <BrandMark size={28} />
            <h2 id="settings-title" className="text-[15px] font-semibold text-[var(--text-primary)]">
              Settings
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-[6px] text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex min-h-0 flex-1">
          <nav className="w-[140px] shrink-0 space-y-0.5 border-r border-[var(--folio-border)] p-2.5">
            {(
              [
                { id: 'profile', label: 'Profile', icon: User },
                { id: 'preferences', label: 'Preferences', icon: Settings2 },
                { id: 'about', label: 'About', icon: Info },
              ] as const
            ).map((item) => {
              const Icon = item.icon
              const active = section === item.id
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSection(item.id)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-[6px] px-2.5 py-2 text-left text-[12px] font-medium transition-colors',
                    active
                      ? 'bg-[var(--surface-1)] text-[var(--text-primary)]'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]',
                  )}
                >
                  <Icon className="h-3.5 w-3.5 stroke-[1.75]" />
                  {item.label}
                </button>
              )
            })}
          </nav>

          <div className="min-w-0 flex-1 overflow-y-auto p-5">
            {section === 'profile' && (
              <div>
                <h3 className="text-[14px] font-semibold">Profile</h3>
                <p className="mt-1 text-[12px] text-[var(--text-secondary)]">
                  Dummy account for the studio shell.
                </p>
                <div className="mt-5 flex items-center gap-3">
                  <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--surface-1)] text-[14px] font-semibold ring-1 ring-[var(--folio-border)]">
                    KS
                  </span>
                  <div>
                    <p className="text-[14px] font-semibold">Kahani Studio</p>
                    <p className="text-[12px] text-[var(--text-secondary)]">maker@kahani.app</p>
                  </div>
                </div>
                <dl className="mt-6 space-y-3 text-[13px]">
                  <div>
                    <dt className="text-[11px] tracking-wide text-[var(--text-secondary)] uppercase">
                      Organization
                    </dt>
                    <dd className="mt-0.5 font-medium">Kahani</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] tracking-wide text-[var(--text-secondary)] uppercase">
                      Role
                    </dt>
                    <dd className="mt-0.5 font-medium">Maker</dd>
                  </div>
                </dl>
              </div>
            )}

            {section === 'preferences' && (
              <div>
                <h3 className="text-[14px] font-semibold">Preferences</h3>
                <p className="mt-1 text-[12px] text-[var(--text-secondary)]">Theme for the studio.</p>
                <div className="mt-5 flex gap-2">
                  {(['light', 'dark', 'system'] as const).map((value) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setTheme(value)}
                      className={cn(
                        'rounded-[6px] px-3 py-1.5 text-[12px] font-medium capitalize transition-colors',
                        theme === value
                          ? 'bg-[var(--brand)] text-white'
                          : 'bg-[var(--surface-1)] text-[var(--text-primary)] hover:bg-[var(--surface-0)]',
                      )}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {section === 'about' && (
              <div>
                <h3 className="text-[14px] font-semibold">About</h3>
                <p className="mt-2 text-[13px] leading-6 text-[var(--text-secondary)]">
                  Kahani Studio is an audio-first story production studio. Prompt the Script Writer
                  agent, ground it with context, and polish drafts in the Editor.
                </p>
              </div>
            )}
          </div>
        </div>
      </aside>
    </div>
  )
}
