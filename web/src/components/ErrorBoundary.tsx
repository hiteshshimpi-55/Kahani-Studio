import { Component, type ErrorInfo, type ReactNode } from 'react'

type Props = { children: ReactNode }
type State = { error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ui_error', error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-3 px-6">
          <h1 className="text-xl font-semibold text-stone-900">Something went wrong</h1>
          <p className="text-sm text-stone-600">{this.state.error.message}</p>
          <button
            type="button"
            className="w-fit rounded border border-stone-400 px-3 py-1.5 text-sm"
            onClick={() => this.setState({ error: null })}
          >
            Try again
          </button>
        </main>
      )
    }
    return this.props.children
  }
}
