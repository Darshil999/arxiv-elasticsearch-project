"use client";

import { useState } from "react";
import type { Paper } from "@/lib/api";
import { ArrowUpRightIcon, FileIcon } from "./Icons";

const MAX_AUTHORS = 4;

function formatDate(date: string | null) {
  if (!date) return null;
  const d = new Date(`${date}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return date;
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
}

function formatAuthors(authors: string[]) {
  if (authors.length <= MAX_AUTHORS) return authors.join(", ");
  return `${authors.slice(0, MAX_AUTHORS).join(", ")} +${authors.length - MAX_AUTHORS} more`;
}

export function ResultCard({ paper, rank }: { paper: Paper; rank: number }) {
  const [expanded, setExpanded] = useState(false);
  const pct = Math.max(0, Math.min(1, paper.score)) * 100;
  const date = formatDate(paper.published);

  return (
    <article className="group rounded-2xl border border-white/[0.06] bg-ink-900/70 p-5 transition hover:border-white/15 hover:bg-ink-900 sm:p-6">
      <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-2 font-mono text-xs text-zinc-500">
        <span className="text-zinc-600">#{String(rank).padStart(2, "0")}</span>
        <div className="flex items-center gap-2" title="Cosine similarity between your query and this paper">
          <span className="text-zinc-500">similarity</span>
          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-ink-700 sm:w-20">
            <div className="h-full rounded-full bg-gradient-to-r from-accent-strong to-signal" style={{ width: `${pct}%` }} />
          </div>
          <span className="tabular-nums text-signal">{paper.score.toFixed(3)}</span>
        </div>
        {date && <span>{date}</span>}
        <span className="text-zinc-600">arXiv:{paper.arxiv_id}</span>
      </div>

      <h2 className="text-lg font-semibold leading-snug text-white sm:text-xl">
        <a href={paper.url} target="_blank" rel="noreferrer" className="decoration-accent/50 underline-offset-4 hover:underline">
          {paper.title}
        </a>
      </h2>

      {paper.authors.length > 0 && <p className="mt-1.5 text-sm text-zinc-400">{formatAuthors(paper.authors)}</p>}

      <p className={`mt-3 text-sm leading-relaxed text-zinc-300 ${expanded ? "" : "line-clamp-3"}`}>{paper.abstract}</p>
      {paper.abstract.length > 280 && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="mt-1 text-xs font-medium text-accent hover:text-white"
          aria-expanded={expanded}
        >
          {expanded ? "Show less" : "Show full abstract"}
        </button>
      )}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          {paper.categories.map((cat) => (
            <span
              key={cat}
              className={`rounded-md border px-2 py-0.5 font-mono text-[11px] ${
                cat === paper.primary_category
                  ? "border-accent/30 bg-accent/10 text-accent"
                  : "border-white/10 bg-white/[0.03] text-zinc-400"
              }`}
            >
              {cat}
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <a
            href={paper.pdf_url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-zinc-300 transition hover:border-white/25 hover:text-white"
          >
            <FileIcon className="h-3.5 w-3.5" /> PDF
          </a>
          <a
            href={paper.url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-ink-950 transition hover:bg-zinc-200"
          >
            View on arXiv <ArrowUpRightIcon className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>
    </article>
  );
}
