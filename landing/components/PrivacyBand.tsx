import { SectionBlurShapes } from "./BlurShapes";

const POINTS = [
  {
    title: "No third-party forms",
    description: "Retro responses are typed straight into your own database — never a Google Form or Typeform.",
  },
  {
    title: "SQLite, one file, one backup",
    description: "The whole dataset lives in a single file you can copy, version, or move whenever you need to.",
  },
  {
    title: "Deployed with one command",
    description: "docker compose up -d and you're running — no cloud account, no vendor lock-in.",
  },
];

export default function PrivacyBand() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <div className="relative overflow-hidden rounded-3xl bg-md-primary px-6 py-16 sm:px-12 sm:py-20">
        <SectionBlurShapes />
        <div className="relative">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-medium tracking-tight text-white sm:text-4xl">
              Your retrospectives stay yours.
            </h2>
            <p className="mt-4 text-white/80">
              The whole point of Sprint Retro is keeping company feedback inside company infrastructure.
            </p>
          </div>

          <div className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-3">
            {POINTS.map((p) => (
              <div
                key={p.title}
                className="rounded-lg border border-white/15 bg-white/10 p-6 backdrop-blur-sm transition-colors duration-300 hover:bg-white/15"
              >
                <h3 className="text-base font-medium text-white">{p.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-white/75">{p.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
