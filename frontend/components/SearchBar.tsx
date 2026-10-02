"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { SearchIcon, SpinnerIcon } from "./Icons";

interface SearchBarProps {
  initialQuery: string;
  loading: boolean;
  onSearch: (query: string) => void;
}

export function SearchBar({ initialQuery, loading, onSearch }: SearchBarProps) {
  const [value, setValue] = useState(initialQuery);
  const [syncedQuery, setSyncedQuery] = useState(initialQuery);
  const inputRef = useRef<HTMLInputElement>(null);

  // Keep the box in sync when the query changes from outside (example chips, back button).
  if (syncedQuery !== initialQuery) {
    setSyncedQuery(initialQuery);
    setValue(initialQuery);
  }

  // "/" focuses the search box, like GitHub and many docs sites.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const q = value.trim();
    if (q.length >= 2) onSearch(q);
  };

  return (
    <form onSubmit={submit} role="search" className="group relative">
      <div className="absolute -inset-px rounded-2xl bg-gradient-to-r from-accent-strong/40 via-white/10 to-signal/30 opacity-60 blur-sm transition group-focus-within:opacity-100" />
      <div className="relative flex items-center gap-2 rounded-2xl border border-white/10 bg-ink-900 p-2 shadow-2xl shadow-black/40">
        <SearchIcon className="ml-2 h-5 w-5 shrink-0 text-zinc-500" />
        <label htmlFor="search-input" className="sr-only">
          Describe the research you are looking for
        </label>
        <input
          id="search-input"
          ref={inputRef}
          type="search"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Describe a research idea…"
          autoComplete="off"
          autoFocus
          maxLength={500}
          className="min-w-0 flex-1 bg-transparent py-2.5 text-base text-white placeholder:text-zinc-500 focus:outline-none sm:text-lg [&::-webkit-search-cancel-button]:hidden"
        />
        <kbd className="hidden rounded border border-white/10 px-1.5 py-0.5 font-mono text-xs text-zinc-500 md:block">
          /
        </kbd>
        <button
          type="submit"
          disabled={loading || value.trim().length < 2}
          className="flex h-11 shrink-0 items-center gap-2 rounded-xl bg-accent-strong px-4 text-sm font-medium text-white transition hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50 sm:px-5"
        >
          {loading ? <SpinnerIcon className="h-4 w-4" /> : null}
          <span>Search</span>
        </button>
      </div>
    </form>
  );
}
