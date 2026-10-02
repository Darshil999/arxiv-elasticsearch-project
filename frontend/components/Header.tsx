import Link from "next/link";
import { API_URL, GITHUB_URL } from "@/lib/config";
import { GithubIcon } from "./Icons";

export function Header() {
  return (
    <header className="relative z-10 border-b border-white/5">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5 text-sm font-medium text-white">
          <Logo />
          <span>
            arxiv<span className="text-accent">/</span>semantic
          </span>
        </Link>
        <nav className="flex items-center gap-1 text-sm text-zinc-400">
          <a
            href={`${API_URL}/docs`}
            target="_blank"
            rel="noreferrer"
            className="rounded-md px-3 py-1.5 transition hover:bg-white/5 hover:text-white"
          >
            API
          </a>
          {GITHUB_URL && (
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 rounded-md px-3 py-1.5 transition hover:bg-white/5 hover:text-white"
            >
              <GithubIcon />
              <span className="hidden sm:inline">GitHub</span>
            </a>
          )}
        </nav>
      </div>
    </header>
  );
}

function Logo() {
  // Three points and their nearest-neighbour links: a tiny vector space.
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
      <rect width="24" height="24" rx="6" fill="#161b25" />
      <path d="M6.5 16.5 12 7.5l5.5 6" stroke="#5b7cff" strokeWidth="1.5" fill="none" />
      <circle cx="6.5" cy="16.5" r="2" fill="#7c9cff" />
      <circle cx="12" cy="7.5" r="2" fill="#e6e9f0" />
      <circle cx="17.5" cy="13.5" r="2" fill="#4ade80" />
    </svg>
  );
}
