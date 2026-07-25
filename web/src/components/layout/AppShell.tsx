import { Outlet } from 'react-router-dom'

export function AppShell() {
  return (
    <div className="min-h-screen bg-[#f3efe6] text-stone-900">
      <header className="border-b border-stone-300/80 bg-[#faf7f0]">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xs tracking-[0.2em] text-stone-500 uppercase">Kissa</p>
            <p className="text-sm text-stone-600">Story production studio</p>
          </div>
        </div>
      </header>
      <Outlet />
    </div>
  )
}
