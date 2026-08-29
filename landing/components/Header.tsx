import Link from "next/link";
import { APP_URL } from "@/lib/config";

export default function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-md-outline/10 bg-md-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <a href="#top" className="flex items-center gap-2.5 font-medium text-md-on-background">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo.svg" alt="" className="h-9 w-auto" />
          <span className="text-base tracking-tight">Sprint Retro</span>
        </a>

        <nav className="hidden items-center gap-1 md:flex">
          <a href="#features" className="md-btn md-btn-text">
            Features
          </a>
          <a href="#how-it-works" className="md-btn md-btn-text">
            How it works
          </a>
          <a href="#faq" className="md-btn md-btn-text">
            FAQ
          </a>
        </nav>

        <Link href={`${APP_URL}/login`} className="md-btn md-btn-filled">
          Login
        </Link>
      </div>
    </header>
  );
}
