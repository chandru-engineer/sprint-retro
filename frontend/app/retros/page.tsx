"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import ProtectedRoute from "@/components/ProtectedRoute";
import StatusBadge from "@/components/StatusBadge";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Project, Retro, RetroStatus, Team } from "@/lib/types";

function RetroListContent() {
  const { user } = useAuth();
  const [retros, setRetros] = useState<Retro[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [projectFilter, setProjectFilter] = useState("");
  const [teamFilter, setTeamFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<RetroStatus | "">("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<Project[]>("/api/projects").then(setProjects).catch(() => {});
    api.get<Team[]>("/api/teams").then(setTeams).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (projectFilter) params.set("project_id", projectFilter);
    if (teamFilter) params.set("team_id", teamFilter);
    if (statusFilter) params.set("status_filter", statusFilter);
    api
      .get<Retro[]>(`/api/retros?${params.toString()}`)
      .then(setRetros)
      .finally(() => setLoading(false));
  }, [projectFilter, teamFilter, statusFilter]);

  const projectName = useMemo(() => {
    const map = new Map(projects.map((p) => [p.id, p.name]));
    return (id: number) => map.get(id) || `#${id}`;
  }, [projects]);

  const teamName = useMemo(() => {
    const map = new Map(teams.map((t) => [t.id, t.name]));
    return (id: number) => map.get(id) || `#${id}`;
  }, [teams]);

  const canCreate = user?.role === "admin" || user?.role === "pmo";

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h1 className="page-title">{user?.role === "member" ? "My Retros" : "Retros"}</h1>
        {canCreate && (
          <Link href="/retros/new" className="btn btn-primary">
            Create Retro
          </Link>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
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

      {loading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : retros.length === 0 ? (
        <p className="text-sm text-slate-400">No retrospectives found.</p>
      ) : (
        <>
          {/* Mobile: card list */}
          <div className="grid gap-3 md:hidden">
            {retros.map((r) => (
              <Link key={r.id} href={`/retros/${r.id}`} className="row-card block active:bg-slate-50">
                <div className="flex items-start justify-between gap-2">
                  <span className="font-semibold text-slate-900">{r.sprint_name}</span>
                  <StatusBadge status={r.status} />
                </div>
                <div className="text-sm text-slate-500 mt-1">
                  {projectName(r.project_id)} · {teamName(r.team_id)}
                </div>
                <div className="text-xs text-slate-400 mt-2">Retro: {r.retro_date}</div>
              </Link>
            ))}
          </div>

          {/* Desktop: table */}
          <div className="data-table-wrap hidden md:block">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Sprint</th>
                  <th>Project</th>
                  <th>Team</th>
                  <th>Retro Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {retros.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50">
                    <td>
                      <Link href={`/retros/${r.id}`} className="font-medium text-brand-600 hover:underline">
                        {r.sprint_name}
                      </Link>
                    </td>
                    <td>{projectName(r.project_id)}</td>
                    <td>{teamName(r.team_id)}</td>
                    <td>{r.retro_date}</td>
                    <td>
                      <StatusBadge status={r.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

export default function RetrosPage() {
  return (
    <ProtectedRoute>
      <div className="page">
        <RetroListContent />
      </div>
    </ProtectedRoute>
  );
}
