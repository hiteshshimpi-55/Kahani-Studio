import {
  Activity,
  ChevronsLeft,
  ChevronsRight,
  Mic2,
  PenLine,
} from 'lucide-react'
import { useState, type ComponentType } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'

import { BrandMark } from '@/components/brand/BrandMark'
import { NavSearch } from '@/components/layout/NavSearch'
import { SidebarProjects } from '@/components/layout/SidebarProjects'
import { ThemeToggle } from '@/components/theme/ThemeToggle'
import { SettingsSheet } from '@/features/settings/components/SettingsSheet'
import { cn } from '@/lib/utils'

function isNavActive(pathname: string, to: string, end = false) {
  if (end) return pathname === to
  return pathname === to || pathname.startsWith(`${to}/`)
}

type SidebarLinkProps = {
  to: string
  label: string
  icon: ComponentType<{ className?: string }>
  end?: boolean
  collapsed: boolean
}

function SidebarLink({ to, label, icon: Icon, end, collapsed }: SidebarLinkProps) {
  const { pathname } = useLocation()
  const active = isNavActive(pathname, to, end)

  return (
    <Link
      to={to}
      title={collapsed ? label : undefined}
      className={cn(
        'flex items-center gap-2.5 rounded-[6px] px-2.5 py-2 text-[14px] font-medium transition-colors',
        'outline-none focus-visible:ring-2 focus-visible:ring-[var(--folio-border-strong)] focus-visible:ring-offset-0',
        collapsed && 'justify-center px-0',
        active
          ? 'bg-[var(--surface-1)] text-[var(--text-primary)]'
          : 'text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]',
      )}
    >
      <Icon
        className={cn(
          'h-[18px] w-[18px] shrink-0 stroke-[1.75]',
          active ? 'text-[var(--text-primary)]' : 'opacity-80',
        )}
      />
      {!collapsed && <span className="flex-1 truncate">{label}</span>}
    </Link>
  )
}

function ProfileButton({
  collapsed,
  onOpenSettings,
}: {
  collapsed: boolean
  onOpenSettings: () => void
}) {
  return (
    <button
      type="button"
      onClick={onOpenSettings}
      title="Open settings"
      className={cn(
        'flex w-full items-center gap-2.5 rounded-[10px] transition-colors hover:bg-[var(--surface-1)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--folio-border-strong)]',
        collapsed ? 'justify-center p-2' : 'px-2 py-2',
      )}
    >
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--surface-1)] text-[12px] font-semibold text-[var(--text-primary)] ring-1 ring-[var(--folio-border)]">
        KS
      </span>
      {!collapsed && (
        <span className="min-w-0 flex-1 text-left">
          <span className="block truncate text-[13px] font-semibold leading-tight text-[var(--text-primary)]">
            Kahani Studio
          </span>
          <span className="mt-0.5 block truncate text-[11px] leading-tight text-[var(--text-secondary)]">
            maker@kahani.app
          </span>
        </span>
      )}
    </button>
  )
}

export function AppShell() {
  const { pathname } = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const isChat = /\/projects\/[^/]+\/chat/.test(pathname)

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-[var(--surface-2)]">
      <aside
        className={cn(
          'hidden h-full shrink-0 flex-col border-r border-[var(--folio-border)] bg-[var(--surface-2)] transition-[width] duration-200 md:flex',
          collapsed ? 'w-[68px]' : 'w-[240px]',
        )}
      >
        <div
          className={cn(
            'flex h-16 shrink-0 items-center border-b border-[var(--folio-border)]',
            collapsed ? 'justify-center px-0' : 'gap-2 px-3',
          )}
        >
          <Link
            to="/"
            title="Kahani Studio"
            className={cn(
              'flex min-w-0 items-center',
              collapsed ? 'justify-center' : 'flex-1 gap-2.5',
            )}
          >
            <BrandMark size={collapsed ? 28 : 32} />
            {!collapsed && (
              <span className="min-w-0 text-left text-[13px] font-semibold leading-snug tracking-tight text-[var(--text-primary)]">
                Kahani
              </span>
            )}
          </Link>
          {!collapsed && (
            <button
              type="button"
              onClick={() => setCollapsed(true)}
              aria-label="Collapse sidebar"
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px] text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]"
            >
              <ChevronsLeft className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {collapsed && (
          <button
            type="button"
            onClick={() => setCollapsed(false)}
            aria-label="Expand sidebar"
            className="mx-auto mt-2.5 flex h-6 w-6 items-center justify-center rounded-[6px] text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]"
          >
            <ChevronsRight className="h-3.5 w-3.5" />
          </button>
        )}

        <div className={cn('flex-1 overflow-y-auto pt-2.5 pb-3', collapsed ? 'px-1.5' : 'px-2.5')}>
          <nav className="space-y-0.5">
            <SidebarProjects collapsed={collapsed} />
            <SidebarLink to="/editor" label="Editor" icon={PenLine} collapsed={collapsed} />
            <SidebarLink to="/voices" label="Voice & SFX" icon={Mic2} collapsed={collapsed} />
            <SidebarLink
              to="/system"
              label="System"
              icon={Activity}
              collapsed={collapsed}
              end
            />
          </nav>
        </div>

        <div
          className={cn(
            'mt-auto border-t border-[var(--folio-border)]',
            collapsed ? 'p-1.5' : 'p-2.5',
          )}
        >
          <ProfileButton collapsed={collapsed} onOpenSettings={() => setSettingsOpen(true)} />
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="grid h-16 shrink-0 grid-cols-[1fr_auto] items-center gap-3 border-b border-[var(--folio-border)] px-4 md:grid-cols-[minmax(0,1fr)_minmax(28rem,40rem)_minmax(0,1fr)] md:px-6">
          <div className="flex min-w-0 items-center gap-2 md:hidden">
            <BrandMark size={24} />
            <p className="truncate text-[14px] font-semibold text-[var(--text-primary)]">Kahani</p>
          </div>
          <div className="hidden md:block" aria-hidden />

          <div className="col-start-1 col-end-2 hidden w-full justify-center md:col-start-2 md:col-end-3 md:flex">
            <NavSearch />
          </div>

          <div className="col-start-2 flex items-center justify-end gap-1 md:col-start-3">
            <ThemeToggle />
            <div className="md:hidden">
              <ProfileButton collapsed onOpenSettings={() => setSettingsOpen(true)} />
            </div>
          </div>
        </header>

        <main
          data-app-scroll
          className={cn(
            'min-h-0 flex-1 bg-[var(--surface-2)]',
            isChat ? 'overflow-hidden p-0' : 'overflow-y-auto p-4 md:p-6',
          )}
        >
          <Outlet />
        </main>
      </div>

      <SettingsSheet open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  )
}
