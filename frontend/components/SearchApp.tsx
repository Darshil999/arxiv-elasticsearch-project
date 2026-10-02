"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, getStats, searchPapers, type SearchResponse, type Stats } from "@/lib/api";
import { CATEGORIES, DEFAULT_LIMIT, EXAMPLE_QUERIES, RESULT_LIMITS } from "@/lib/config";
import { HowItWorks } from "./HowItWorks";
import { XIcon } from "./Icons";
import { ResultCard } from "./ResultCard";
import { SearchBar } from "./SearchBar";
import { EmptyState, ErrorState, ResultsSkeleton } from "./States";

type Outcome = { key: string; data: SearchResponse; error?: never } | { key: string; error: string; data?: never };

const SLOW_REQUEST_MS = 4000;

function parseLimit(raw: string | null) {
  const n = Number(raw);
  return (RESULT_LIMITS as readonly number[]).includes(n) ? n : DEFAULT_LIMIT;
}

export function SearchApp() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  // The URL is the single source of truth, so searches survive refreshes and can be shared.
  const query = (params.get("q") ?? "").trim();
  const limit = parseLimit(params.get("limit"));
  const categories = (params.get("cat") ?? "").split(",").filter((c) => CATEGORIES.some((k) => k.id === c));

  const [attempt, setAttempt] = useState(0);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [slowKey, setSlowKey] = useState<string | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);

  const requestKey = query.length >= 2 ? JSON.stringify([query, limit, categories, attempt]) : null;
  const loading = requestKey !== null && outcome?.key !== requestKey;

  useEffect(() => {
    // Also wakes up a sleeping free-tier backend as soon as the page opens.
    const controller = new AbortController();
    getStats(controller.signal).then(setStats, () => {});
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!requestKey) return;
    const [q, lim, cats] = JSON.parse(requestKey) as [string, number, string[]];
    const controller = new AbortController();
    const slowTimer = setTimeout(() => setSlowKey(requestKey), SLOW_REQUEST_MS);

    searchPapers({ query: q, limit: lim, categories: cats }, controller.signal)
      .then((data) => setOutcome({ key: requestKey, data }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setOutcome({ key: requestKey, error: err instanceof ApiError ? err.message : "Something went wrong." });
      })
      .finally(() => clearTimeout(slowTimer));

    return () => {
      controller.abort();
      clearTimeout(slowTimer);
    };
  }, [requestKey]);

  const updateUrl = (next: { q?: string; limit?: number; cat?: string[] }) => {
    const sp = new URLSearchParams(params.toString());
    const set = (key: string, value: string | null) => (value ? sp.set(key, value) : sp.delete(key));
    if (next.q !== undefined) set("q", next.q);
    if (next.limit !== undefined) set("limit", next.limit === DEFAULT_LIMIT ? null : String(next.limit));
    if (next.cat !== undefined) set("cat", next.cat.join(","));
    const qs = sp.toString();
    router.push(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  };

  const toggleCategory = (id: string) =>
    updateUrl({ cat: categories.includes(id) ? categories.filter((c) => c !== id) : [...categories, id] });

  const current = outcome && outcome.key === requestKey ? outcome : null;

  return (
    <>
      <section className="relative">
        <div className="mx-auto max-w-3xl pt-14 text-center sm:pt-20">
          <p className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 font-mono text-[11px] text-zinc-400">
            <span className="h-1.5 w-1.5 rounded-full bg-signal shadow-[0_0_8px] shadow-signal" />
            {stats ? `${stats.papers_indexed.toLocaleString()} papers indexed` : "vector search"} · MiniLM-L6 · Qdrant
          </p>
          <h1 className="mt-5 text-4xl font-semibold tracking-tight text-white sm:text-6xl">
            ArXiv Semantic Search
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base text-zinc-400 sm:text-lg">
            Discover research papers by <span className="text-white">meaning</span>, not just keywords. Describe an
            idea in plain language and get the most relevant computer-science papers.
          </p>
        </div>

        <div className="mx-auto mt-10 max-w-3xl">
          <SearchBar initialQuery={query} loading={loading} onSearch={(q) => updateUrl({ q })} />

          <div className="mt-4 flex flex-wrap items-center gap-2">
            {CATEGORIES.map((cat) => {
              const active = categories.includes(cat.id);
              return (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => toggleCategory(cat.id)}
                  title={cat.label}
                  aria-pressed={active}
                  className={`rounded-lg border px-2.5 py-1 font-mono text-xs transition ${
                    active
                      ? "border-accent/50 bg-accent/15 text-accent"
                      : "border-white/10 text-zinc-400 hover:border-white/20 hover:text-zinc-200"
                  }`}
                >
                  {cat.id}
                </button>
              );
            })}
            {categories.length > 0 && (
              <button
                type="button"
                onClick={() => updateUrl({ cat: [] })}
                className="flex items-center gap-1 px-1.5 py-1 text-xs text-zinc-500 hover:text-white"
              >
                <XIcon className="h-3 w-3" /> clear
              </button>
            )}
            <label className="ml-auto flex items-center gap-2 text-xs text-zinc-500">
              Results
              <select
                value={limit}
                onChange={(e) => updateUrl({ limit: Number(e.target.value) })}
                className="rounded-lg border border-white/10 bg-ink-900 px-2 py-1 font-mono text-xs text-zinc-200 focus:border-accent/50 focus:outline-none"
              >
                {RESULT_LIMITS.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </section>

      <section className="mx-auto mt-10 w-full max-w-3xl pb-20" aria-live="polite">
        {!requestKey && (
          <>
            <div className="mb-12">
              <h2 className="mb-3 font-mono text-xs uppercase tracking-widest text-zinc-500">Try an example</h2>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_QUERIES.map((example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => updateUrl({ q: example })}
                    className="rounded-full border border-white/10 bg-white/[0.02] px-3.5 py-1.5 text-sm text-zinc-300 transition hover:border-accent/40 hover:bg-accent/10 hover:text-white"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
            <HowItWorks />
          </>
        )}

        {loading && <ResultsSkeleton slow={slowKey === requestKey} />}

        {current?.error && <ErrorState message={current.error} onRetry={() => setAttempt((a) => a + 1)} />}

        {current?.data && current.data.count === 0 && (
          <EmptyState query={current.data.query} filtered={categories.length > 0} />
        )}

        {current?.data && current.data.count > 0 && (
          <>
            <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2 border-b border-white/5 pb-3 text-sm">
              <p className="text-zinc-400">
                <span className="font-medium text-white">{current.data.count}</span> most similar papers for{" "}
                <span className="text-white">&ldquo;{current.data.query}&rdquo;</span>
              </p>
              <p className="font-mono text-xs text-zinc-500">{current.data.took_ms.toFixed(0)} ms</p>
            </div>
            <div className="space-y-4">
              {current.data.results.map((paper, i) => (
                <ResultCard key={paper.arxiv_id} paper={paper} rank={i + 1} />
              ))}
            </div>
          </>
        )}
      </section>
    </>
  );
}
