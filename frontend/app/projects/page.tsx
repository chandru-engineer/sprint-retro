"use client";

import { FormEvent, useEffect, useState } from "react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { api, ApiError } from "@/lib/api";
import { Project, ProjectStatus, Team } from "@/lib/types";

function ProjectForm({ teams, onSaved }: { teams: Team[]; onSaved: () => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [teamId, setTeamId] = useState("");
  const [status, setStatus] = useState<ProjectStatus>("active");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await api.post<Project>("/api/projects", { name, description, team_id: Number(teamId), status });
      setName("");
      setDescription("");
      setTeamId("");
      setStatus("active");
      onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create project.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card space-y-3">
      <h2 className="font-semibold text-slate-900">Create Project</h2>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <input
          required
          className="input"
          placeholder="Project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="input"
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <select required className="input" value={teamId} onChange={(e) => setTeamId(e.target.value)}>
          <option value="">Select team</option>
          {teams.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value as ProjectStatus)}>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>
      <button type="submit" disabled={submitting} className="btn btn-primary">
        {submitting ? "Creating..." : "Create Project"}
      </button>
    </form>
  );
}

function ProjectsContent() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [error, setError] = useState("");

  function load() {
    api.get<Project[]>("/api/projects").then(setProjects).catch(() => setError("Could not load projects."));
    api.get<Team[]>("/api/teams").then(setTeams).catch(() => {});
  }

  useEffect(load, []);

  const teamName = (id: number) => teams.find((t) => t.id === id)?.name || `#${id}`;

  return (
    <div className="space-y-6">
      <h1 className="page-title">Projects</h1>
      <ProjectForm teams={teams} onSaved={load} />
      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* Mobile: card list */}
      <div className="grid gap-3 md:hidden">
        {projects.map((p) => (
          <div key={p.id} className="row-card">
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="font-semibold text-slate-900">{p.name}</div>
                {p.description && <div className="text-sm text-slate-500">{p.description}</div>}
              </div>
              <span className={`badge ${p.status === "active" ? "badge-submitted" : "badge-draft"}`}>{p.status}</span>
            </div>
            <div className="text-xs text-slate-400 mt-2">{teamName(p.team_id)}</div>
          </div>
        ))}
      </div>

      {/* Desktop: table */}
      <div className="data-table-wrap hidden md:block">
        <table className="data-table">
          <thead>
            <tr>
              <th>Project</th>
              <th>Team</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((p) => (
              <tr key={p.id}>
                <td>
                  <div className="font-medium">{p.name}</div>
                  {p.description && <div className="text-xs text-slate-400">{p.description}</div>}
                </td>
                <td>{teamName(p.team_id)}</td>
                <td>
                  <span className={`badge ${p.status === "active" ? "badge-submitted" : "badge-draft"}`}>
                    {p.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function ProjectsPage() {
  return (
    <ProtectedRoute allow={["admin"]}>
      <div className="page">
        <ProjectsContent />
      </div>
    </ProtectedRoute>
  );
}
