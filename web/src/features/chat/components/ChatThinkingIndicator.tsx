export function ChatThinkingIndicator() {
  return (
    <div className="my-2 flex items-center gap-2 text-[13px] text-[var(--text-secondary)] italic">
      <span className="chat-thinking-dots flex gap-1">
        <span>•</span>
        <span>•</span>
        <span>•</span>
      </span>
      Orchestrating Script Writer…
    </div>
  )
}
