"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import ProtectedRoute from "@/components/ProtectedRoute";
import StatusBadge from "@/components/StatusBadge";
import { api } from "@/lib/api";
import { Project, RetroStatus, RetroSummary, Team, User } from "@/lib/types";

function SearchIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card">
      <div className="text-2xl sm:text-3xl font-bold text-slate-900">{value}</div>
      <div className="text-sm text-slate-500 mt-1">{label}</div>
    </div>
  );
}

function ProgressBar({ percent }: { percent: number }) {
  return (
    <div className="h-2 w-full rounded-full bg-md-surface-container-low overflow-hidden">
      <div
        className="h-full rounded-full bg-md-primary transition-all duration-300 ease-emphasized"
        style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
      />
    </div>
  );
}

function RetroCard({ retro }: { retro: RetroSummary }) {
  return (
    <div className="card flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <Link href={`/retros/${retro.id}`} className="font-semibold text-slate-900 hover:underline truncate block">
            {retro.sprint_name}
          </Link>
          <div className="text-sm text-slate-500 truncate">
            {retro.project_name} &middot; {retro.team_name}
          </div>
        </div>
        <StatusBadge status={retro.status} />
      </div>

      <div className="text-xs text-slate-400">
        Retro meeting: {retro.retro_date} {retro.retro_time}
      </div>

      <div>
        <div className="flex items-center justify-between text-sm mb-1.5">
          <span className="text-slate-600">
            {retro.submitted_count} / {retro.total_count} submitted
          </span>
          <span className="font-semibold text-md-primary">{retro.completion_percent}%</span>
        </div>
        <ProgressBar percent={retro.completion_percent} />
      </div>

      <div className="flex flex-wrap gap-2 pt-1">
        <Link href={`/retros/${retro.id}`} className="btn btn-secondary btn-sm">
          View
        </Link>
        <Link href={`/retros/${retro.id}/responses`} className="btn btn-secondary btn-sm">
          Responses
        </Link>
        <Link href={`/retros/${retro.id}/report`} className="btn btn-secondary btn-sm">
          Report
        </Link>
      </div>
    </div>
  );
}

function RetroDashboardContent() {
  const [retros, setRetros] = useState<RetroSummary[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [search, setSearch] = useState("");
  const [projectFilter, setProjectFilter] = useState("");
  const [teamFilter, setTeamFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<RetroStatus | "">("");
  const [userFilter, setUserFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<Project[]>("/api/projects").then(setProjects).catch(() => {});
    api.get<Team[]>("/api/teams").then(setTeams).catch(() => {});
    api.get<User[]>("/api/users").then(setUsers).catch(() => {});
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(true);
      setError("");
      const params = new URLSearchParams();
      if (search.trim()) params.set("q", search.trim());
      if (projectFilter) params.set("project_id", projectFilter);
      if (teamFilter) params.set("team_id", teamFilter);
      if (statusFilter) params.set("status_filter", statusFilter);
      if (userFilter) params.set("user_id", userFilter);
      api
        .get<RetroSummary[]>(`/api/retros/dashboard?${params.toString()}`)
        .then(setRetros)
        .catch(() => setError("Could not load the retro dashboard."))
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(timer);
  }, [search, projectFilter, teamFilter, statusFilter, userFilter]);

  const stats = useMemo(() => {
    const total = retros.length;
    const open = retros.filter((r) => r.status === "open").length;
    const completed = retros.filter((r) => r.status === "completed").length;
    const draft = retros.filter((r) => r.status === "draft").length;
    const avgCompletion = total
      ? Math.round((retros.reduce((sum, r) => sum + r.completion_percent, 0) / total) * 10) / 10
      : 0;
    return { total, open, completed, draft, avgCompletion };
  }, [retros]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="page-title">Retro Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">Every retrospective across the organization, at a glance.</p>
        </div>
        <Link href="/retros/new" className="btn btn-primary shrink-0">
          Create Retro
        </Link>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <StatTile label="Total" value={stats.total} />
        <StatTile label="Open" value={stats.open} />
        <StatTile label="Draft" value={stats.draft} />
        <StatTile label="Completed" value={stats.completed} />
        <StatTile label="Avg. Completion" value={`${stats.avgCompletion}%`} />
      </div>

      <div className="card space-y-3">
        <div className="relative">
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">
            <SearchIcon />
          </span>
          <input
            className="input pl-10"
            placeholder="Search by sprint, project, or team..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <select className="input" value={projectFilter} onChange={(e) => setProjectFilter(e.target.value)}>
            <option value="">All Projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <select className="input" value={teamFilter} onChange={(e) => setTeamFilter(e.target.value)}>
            <option value="">All Teams</option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <select className="input" value={userFilter} onChange={(e) => setUserFilter(e.target.value)}>
            <option value="">All Users</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
          <select
            className="input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as RetroStatus | "")}
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="open">Open</option>
            <option value="completed">Completed</option>
          </select>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : retros.length === 0 ? (
        <p className="text-sm text-slate-400">No retrospectives match your search.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {retros.map((r) => (
            <RetroCard key={r.id} retro={r} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function RetroDashboardPage() {
  return (
    <ProtectedRoute allow={["admin", "pmo"]}>
      <div className="page">
        <RetroDashboardContent />
      </div>
    </ProtectedRoute>
  );
}
