import { AlertIcon, SearchIcon } from "./Icons";

export function ResultsSkeleton({ slow }: { slow: boolean }) {
  return (
    <div aria-busy="true" aria-live="polite">
      {slow && (
        <p className="mb-4 rounded-xl border border-amber-400/20 bg-amber-400/5 px-4 py-3 text-sm text-amber-200/90">
          Waking up the search server… The free-tier backend sleeps when idle, so the first search after a quiet period
          can take 1–2 minutes. Later searches are fast.
        </p>
      )}
      <div className="space-y-4">
        {Array.from({ length: 3 }, (_, i) => (
          <div key={i} className="rounded-2xl border border-white/[0.06] bg-ink-900/70 p-6">
            <div className="skeleton h-3 w-48 rounded" />
            <div className="skeleton mt-4 h-5 w-4/5 rounded" />
            <div className="skeleton mt-2 h-3 w-1/3 rounded" />
            <div className="skeleton mt-4 h-3 w-full rounded" />
            <div className="skeleton mt-2 h-3 w-full rounded" />
            <div className="skeleton mt-2 h-3 w-2/3 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function EmptyState({ query, filtered }: { query: string; filtered: boolean }) {
  return (
    <div className="rounded-2xl border border-dashed border-white/10 px-6 py-14 text-center">
      <SearchIcon className="mx-auto h-6 w-6 text-zinc-600" />
      <h2 className="mt-3 font-medium text-white">No papers found</h2>
      <p className="mx-auto mt-1 max-w-md text-sm text-zinc-400">
        Nothing matched &ldquo;{query}&rdquo;
        {filtered ? " in the selected categories. Try clearing the category filters." : ". Try describing the idea differently."}
      </p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="rounded-2xl border border-red-400/20 bg-red-400/5 px-6 py-8 text-center">
      <AlertIcon className="mx-auto h-6 w-6 text-red-300" />
      <h2 className="mt-3 font-medium text-white">Search failed</h2>
      <p className="mx-auto mt-1 max-w-md text-sm text-zinc-400">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-5 rounded-lg border border-white/15 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/5"
      >
        Try again
      </button>
    </div>
  );
}
