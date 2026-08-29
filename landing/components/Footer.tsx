import Link from "next/link";
import { APP_URL } from "@/lib/config";

export default function Footer() {
  return (
    <footer className="border-t border-md-outline/10">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-10 sm:flex-row sm:px-6">
        <div className="flex items-center gap-2.5 text-md-on-background">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo.svg" alt="" className="h-8 w-auto" />
          <span className="text-sm font-medium">Sprint Retro</span>
        </div>
        <p className="text-sm text-md-on-surface-variant">
          Self-hosted sprint retrospectives. Collected, stored, and reported — privately.
        </p>
        <Link href={`${APP_URL}/login`} className="md-btn md-btn-text">
          Login
        </Link>
      </div>
    </footer>
  );
}
