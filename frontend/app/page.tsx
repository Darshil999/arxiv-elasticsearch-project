import { Suspense } from "react";
import { Header } from "@/components/Header";
import { SearchApp } from "@/components/SearchApp";

export default function Home() {
  return (
    <>
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[640px] overflow-hidden" aria-hidden="true">
        <div className="bg-grid absolute inset-0" />
        <div className="glow absolute inset-0" />
      </div>

      <Header />

      <main className="relative flex-1 px-4 sm:px-6">
        {/* SearchApp reads the URL query string, which requires a Suspense boundary for prerendering. */}
        <Suspense fallback={<div className="min-h-[60vh]" />}>
          <SearchApp />
        </Suspense>
      </main>

      <footer className="relative border-t border-white/5 px-4 py-6 text-center text-xs text-zinc-500 sm:px-6">
        Paper metadata from{" "}
        <a href="https://arxiv.org" target="_blank" rel="noreferrer" className="text-zinc-400 hover:text-white">
          arXiv.org
        </a>
        . Thank you to arXiv for use of its open access interoperability. Built with Next.js, FastAPI and Qdrant.
      </footer>
    </>
  );
}
