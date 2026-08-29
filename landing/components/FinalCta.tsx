import Link from "next/link";
import { HeroBlurShapes } from "./BlurShapes";
import { APP_URL } from "@/lib/config";

export default function FinalCta() {
  return (
    <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6 sm:pb-28">
      <div className="relative overflow-hidden rounded-3xl bg-md-surface-container px-6 py-16 text-center sm:px-12 sm:py-20 shadow-lg">
        <HeroBlurShapes />
        <div className="relative">
          <h2 className="mx-auto max-w-xl text-3xl font-medium tracking-tight text-md-on-background sm:text-4xl">
            Ready to run your next retro?
          </h2>
          <p className="mx-auto mt-4 max-w-md text-md-on-surface-variant">
            Log in, create a retro, and invite your team — it takes less time than the meeting itself.
          </p>
          <div className="mt-8">
            <Link href={`${APP_URL}/login`} className="md-btn md-btn-filled h-12 px-8 text-base">
              Open Sprint Retro
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
