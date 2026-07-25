import { NavLink, Outlet } from 'react-router-dom'

import { cn } from '@/lib/utils'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'text-sm font-medium transition-colors',
    isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground',
  )

export function AppShell() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4">
          <div className="flex items-center gap-8">
            <NavLink to="/" className="group">
              <p className="text-lg font-bold tracking-tight text-foreground group-hover:text-primary">
                Kissa
              </p>
              <p className="text-xs text-muted-foreground">Story production studio</p>
            </NavLink>
            <nav className="flex items-center gap-4">
              <NavLink to="/" end className={navLinkClass}>
                Projects
              </NavLink>
              <NavLink to="/system" className={navLinkClass}>
                System
              </NavLink>
            </nav>
          </div>
        </div>
      </header>
      <Outlet />
    </div>
  )
}
