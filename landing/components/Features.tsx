const FEATURES: { title: string; description: string; icon: React.ReactNode }[] = [
  {
    title: "Five focused questions",
    description:
      "Achievements, what went well, what didn't, learnings, and improvements. No voting, no clutter — just the retro.",
    icon: (
      <path d="M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
    ),
  },
  {
    title: "Draft, then submit",
    description: "Team members can save a draft and come back later. Once submitted, a response is locked and read-only.",
    icon: <path d="M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5Z" />,
  },
  {
    title: "Live participation tracking",
    description: "PMOs see exactly who has submitted and who hasn't, with a running completion percentage.",
    icon: <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />,
  },
  {
    title: "Consolidated reports",
    description: "One click turns every submitted response into a clean, print-friendly retrospective report.",
    icon: <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6ZM14 2v6h6M16 13H8M16 17H8M10 9H8" />,
  },
  {
    title: "Three simple roles",
    description: "Admin, PMO / Team Lead, and Team Member. No complicated permission matrix to configure.",
    icon: <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" />,
  },
  {
    title: "Self-hosted & private",
    description: "SQLite + Docker Compose. Your team's retrospective data never leaves your own infrastructure.",
    icon: <path d="M12 2 3 6v6c0 5 3.8 9 9 10 5.2-1 9-5 9-10V6l-9-4Z" />,
  },
];

export default function Features() {
  return (
    <section id="features" className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
      <div className="mx-auto max-w-2xl text-center">
        <span className="md-chip">Built for the actual workflow</span>
        <h2 className="mt-5 text-3xl font-medium tracking-tight text-md-on-background sm:text-4xl">
          Everything a retro needs. Nothing it doesn&rsquo;t.
        </h2>
        <p className="mt-4 text-md-on-surface-variant">
          No action items, no issue tracker, no AI summaries. Sprint Retro collects, stores, and reports — that&rsquo;s it.
        </p>
      </div>

      <div className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="group rounded-lg bg-md-surface-container p-7 shadow-sm transition-all duration-300 ease-emphasized hover:scale-[1.02] hover:shadow-md"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-md-primary-container text-md-on-primary-container">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                {f.icon}
              </svg>
            </div>
            <h3 className="mt-5 text-lg font-medium text-md-on-background">{f.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-md-on-surface-variant">{f.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
