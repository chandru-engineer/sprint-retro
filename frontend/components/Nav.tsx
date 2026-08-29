"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import OrgSwitcher from "@/components/OrgSwitcher";

function NavLink({ href, children, onClick }: { href: string; children: React.ReactNode; onClick?: () => void }) {
  const pathname = usePathname();
  const active =
    pathname === href ||
    (href !== "/dashboard" &&
      href !== "/retros/dashboard" &&
      pathname?.startsWith(href) &&
      !pathname?.startsWith("/retros/dashboard"));
  return (
    <Link
      href={href}
      onClick={onClick}
      className={`px-4 py-2.5 md:py-2 rounded-full text-sm font-medium transition-colors duration-300 ease-emphasized ${
        active ? "bg-md-primary-container text-md-on-primary-container" : "text-slate-600 hover:bg-slate-100"
      }`}
    >
      {children}
    </Link>
  );
}

function MenuIcon({ open }: { open: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      {open ? (
        <path d="M6 6l12 12M18 6L6 18" />
      ) : (
        <path d="M4 7h16M4 12h16M4 17h16" />
      )}
    </svg>
  );
}

export default function Nav() {
  const { user, logout } = useAuth();
  const [appName, setAppName] = useState("Sprint Retro");
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    api
      .get<{ app_name: string }>("/api/config")
      .then((cfg) => {
        setAppName(cfg.app_name);
        document.title = cfg.app_name;
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  if (!user) return null;

  const links = (
    <>
      <NavLink href="/dashboard" onClick={() => setMenuOpen(false)}>
        Dashboard
      </NavLink>
      <NavLink href="/retros" onClick={() => setMenuOpen(false)}>
        {user.role === "member" ? "My Retros" : "Retros"}
      </NavLink>
      {(user.role === "admin" || user.role === "pmo") && (
        <NavLink href="/retros/dashboard" onClick={() => setMenuOpen(false)}>
          Retro Dashboard
        </NavLink>
      )}
      {user.role === "admin" && (
        <>
          <NavLink href="/teams" onClick={() => setMenuOpen(false)}>
            Teams
          </NavLink>
          <NavLink href="/projects" onClick={() => setMenuOpen(false)}>
            Projects
          </NavLink>
          <NavLink href="/users" onClick={() => setMenuOpen(false)}>
            Users
          </NavLink>
          <NavLink href="/settings" onClick={() => setMenuOpen(false)}>
            Settings
          </NavLink>
        </>
      )}
    </>
  );

  return (
    <header className="border-b border-slate-200/70 bg-md-background/90 backdrop-blur-md sticky top-0 z-40">
      <div className="page !py-0">
        <div className="flex items-center justify-between h-16 md:h-16 gap-3">
          <div className="flex items-center gap-6 min-w-0">
            <span className="flex items-center gap-2.5 shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/logo.svg" alt="" className="h-8 w-auto" />
              <span className="font-medium text-slate-900 tracking-tight hidden sm:inline">{appName}</span>
            </span>
            <nav className="hidden md:flex items-center gap-1">{links}</nav>
          </div>

          <div className="hidden md:flex items-center gap-3 shrink-0">
            <OrgSwitcher />
            <span className="text-sm text-slate-500 truncate max-w-[220px]">
              {user.name} <span className="text-slate-400">({user.role})</span>
            </span>
            <button className="btn btn-secondary btn-sm" onClick={logout}>
              Logout
            </button>
          </div>

          <button
            className="md:hidden flex items-center justify-center h-11 w-11 -mr-2 rounded-full text-slate-600 hover:bg-slate-100 transition-colors duration-300 ease-emphasized"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <MenuIcon open={menuOpen} />
          </button>
        </div>
      </div>

      {menuOpen && (
        <div className="md:hidden border-t border-slate-200/70 bg-md-background">
          <div className="page !py-3 flex flex-col gap-1">
            {links}
            <div className="mt-2 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
              <span className="text-sm text-slate-500 truncate">
                {user.name} <span className="text-slate-400">({user.role})</span>
              </span>
              <OrgSwitcher />
              <button className="btn btn-secondary btn-sm shrink-0" onClick={logout}>
                Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
