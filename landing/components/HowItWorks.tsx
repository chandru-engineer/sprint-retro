const STEPS = [
  { title: "Create the retro", description: "PMO picks a project, team, and sprint, then sets the retro meeting date." },
  { title: "Invite the team", description: "Select participants and click Notify Team — invitation emails go out immediately." },
  { title: "Team fills the form", description: "Five questions, save as draft anytime, submit when ready." },
  { title: "Track participation", description: "Watch submissions roll in with a live completion percentage." },
  { title: "Review responses", description: "Browse by question or open any one person's full response." },
  { title: "Generate the report", description: "A consolidated, print-ready report — no manual copy-paste." },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="relative overflow-hidden bg-md-surface-container-low py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto max-w-2xl text-center">
          <span className="md-chip">Six steps, start to finish</span>
          <h2 className="mt-5 text-3xl font-medium tracking-tight text-md-on-background sm:text-4xl">How it works</h2>
          <p className="mt-4 text-md-on-surface-variant">
            The same process your PMO runs today &mdash; minus the external form and the manual consolidation.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
          {STEPS.map((step, i) => (
            <div key={step.title} className="group relative flex gap-4">
              <div className="relative shrink-0">
                <div
                  aria-hidden="true"
                  className="absolute -inset-2 rounded-full bg-md-tertiary/25 opacity-0 blur-lg transition-opacity duration-300 group-hover:opacity-100"
                />
                <div className="relative flex h-11 w-11 items-center justify-center rounded-full bg-md-tertiary text-base font-medium text-white">
                  {i + 1}
                </div>
              </div>
              <div>
                <h3 className="pt-1.5 text-base font-medium text-md-on-background">{step.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-md-on-surface-variant">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
