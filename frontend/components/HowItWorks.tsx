const STEPS = [
  {
    title: "Embed the query",
    body: "Your text is encoded by all-MiniLM-L6-v2 into a 384-dimensional vector that captures its meaning.",
    tag: "FastAPI · ONNX",
  },
  {
    title: "Nearest-neighbour search",
    body: "Qdrant compares it against pre-computed embeddings of every paper's title and abstract using cosine similarity.",
    tag: "Qdrant · HNSW",
  },
  {
    title: "Ranked by meaning",
    body: "Papers come back ranked by similarity, so they match even when they share no keywords with your query.",
    tag: "Top-k results",
  },
];

export function HowItWorks() {
  return (
    <section aria-labelledby="how-it-works" className="mt-4">
      <h2 id="how-it-works" className="mb-4 font-mono text-xs uppercase tracking-widest text-zinc-500">
        How it works
      </h2>
      <ol className="grid gap-3 md:grid-cols-3">
        {STEPS.map((step, i) => (
          <li key={step.title} className="rounded-2xl border border-white/[0.06] bg-ink-900/60 p-5">
            <div className="flex items-center justify-between font-mono text-xs">
              <span className="text-accent">0{i + 1}</span>
              <span className="text-zinc-600">{step.tag}</span>
            </div>
            <h3 className="mt-3 font-medium text-white">{step.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-zinc-400">{step.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
