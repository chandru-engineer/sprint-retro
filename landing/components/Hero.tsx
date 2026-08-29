import Link from "next/link";
import { HeroBlurShapes } from "./BlurShapes";
import { APP_URL } from "@/lib/config";

const WORKFLOW = ["Create Retro", "Invite Team", "Team Fills Form", "Review Responses", "Get Report"];

export default function Hero() {
  return (
    <section id="top" className="mx-auto max-w-6xl px-4 pt-10 sm:px-6 sm:pt-16">
      <div className="relative overflow-hidden rounded-[32px] bg-md-surface-container px-6 py-16 text-center sm:rounded-3xl sm:px-12 sm:py-24">
        <HeroBlurShapes />

        <div className="relative">
          <span className="md-chip">Self-hosted &middot; Your data, your servers</span>

          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-medium leading-[1.15] tracking-tight text-md-on-background sm:text-5xl md:text-[3.5rem]">
            Collect the team&rsquo;s voice.
            <br className="hidden sm:block" /> Keep the data private.
          </h1>

          <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-md-on-surface-variant">
            Sprint Retro replaces the external retro form your PMO copies into a doc. Create a retro, invite the
            team, collect five honest answers each, and get a consolidated report — automatically.
          </p>

          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href={`${APP_URL}/login`} className="md-btn md-btn-filled h-12 px-8 text-base">
              Open Sprint Retro
            </Link>
            <a href="#how-it-works" className="md-btn md-btn-outlined h-12 px-8 text-base">
              See how it works
            </a>
          </div>

          <div className="mx-auto mt-14 flex max-w-3xl flex-wrap items-center justify-center gap-2">
            {WORKFLOW.map((step, i) => (
              <div key={step} className="flex items-center gap-2">
                <span className="rounded-full bg-white/70 px-4 py-2 text-sm font-medium text-md-on-surface-variant shadow-sm backdrop-blur-sm">
                  {step}
                </span>
                {i < WORKFLOW.length - 1 && (
                  <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="text-md-outline">
                    <path d="M9 6l6 6-6 6" />
                  </svg>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
