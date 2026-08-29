"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ProtectedRoute from "@/components/ProtectedRoute";
import { api, ApiError } from "@/lib/api";
import { Project, Team } from "@/lib/types";

function CreateRetroForm() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [projectId, setProjectId] = useState("");
  const [teamId, setTeamId] = useState("");
  const [sprintName, setSprintName] = useState("");
  const [sprintStart, setSprintStart] = useState("");
  const [sprintEnd, setSprintEnd] = useState("");
  const [retroDate, setRetroDate] = useState("");
  const [retroTime, setRetroTime] = useState("10:00");
  const [selectedMembers, setSelectedMembers] = useState<Set<number>>(new Set());

  useEffect(() => {
    api.get<Project[]>("/api/projects").then(setProjects).catch(() => {});
    api.get<Team[]>("/api/teams").then(setTeams).catch(() => {});
  }, []);

  const selectedTeam = teams.find((t) => String(t.id) === teamId);

  useEffect(() => {
    setSelectedMembers(new Set());
  }, [teamId]);

  function toggleMember(id: number) {
    setSelectedMembers((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const retro = await api.post<{ id: number }>("/api/retros", {
        project_id: Number(projectId),
        team_id: Number(teamId),
        name: `${sprintName} Retrospective`,
        sprint_name: sprintName,
        sprint_start_date: sprintStart,
        sprint_end_date: sprintEnd,
        retro_date: retroDate,
        retro_time: `${retroTime}:00`,
        participant_ids: Array.from(selectedMembers),
      });
      router.push(`/retros/${retro.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create retrospective.");
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="page-title mb-6">Create Retro</h1>
      <form onSubmit={handleSubmit} className="card space-y-4">
        {error && <div className="alert alert-error">{error}</div>}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Project</label>
            <select required className="input" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              <option value="">Select project</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Team</label>
            <select required className="input" value={teamId} onChange={(e) => setTeamId(e.target.value)}>
              <option value="">Select team</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="label">Sprint Name</label>
          <input
            required
            className="input"
            placeholder="Sprint 25"
            value={sprintName}
            onChange={(e) => setSprintName(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Sprint Start Date</label>
            <input
              type="date"
              required
              className="input"
              value={sprintStart}
              onChange={(e) => setSprintStart(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Sprint End Date</label>
            <input
              type="date"
              required
              className="input"
              value={sprintEnd}
              onChange={(e) => setSprintEnd(e.target.value)}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Retro Meeting Date</label>
            <input
              type="date"
              required
              className="input"
              value={retroDate}
              onChange={(e) => setRetroDate(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Retro Meeting Time</label>
            <input
              type="time"
              required
              className="input"
              value={retroTime}
              onChange={(e) => setRetroTime(e.target.value)}
            />
          </div>
        </div>

        {selectedTeam && (
          <div>
            <label className="label">Invite Team Members</label>
            <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 max-h-56 overflow-y-auto">
              {selectedTeam.members.length === 0 && (
                <p className="text-sm text-slate-400 px-3 py-3">This team has no members yet.</p>
              )}
              {selectedTeam.members.map((m) => (
                <label key={m.id} className="flex items-center gap-2.5 px-3 py-3 text-sm cursor-pointer active:bg-slate-50">
                  <input
                    type="checkbox"
                    className="h-4 w-4 shrink-0 accent-brand-600"
                    checked={selectedMembers.has(m.id)}
                    onChange={() => toggleMember(m.id)}
                  />
                  <span className="truncate">
                    {m.name} <span className="text-slate-400">({m.email})</span>
                  </span>
                </label>
              ))}
            </div>
          </div>
        )}

        <button type="submit" disabled={submitting} className="btn btn-primary w-full sm:w-auto">
          {submitting ? "Creating..." : "Create Retro"}
        </button>
        <p className="text-xs text-slate-400 -mt-2">
          The retro is created as a draft. Use the Notify Team button on the retro page when you're ready to email
          invited members.
        </p>
      </form>
    </div>
  );
}

export default function NewRetroPage() {
  return (
    <ProtectedRoute allow={["admin", "pmo"]}>
      <div className="page">
        <CreateRetroForm />
      </div>
    </ProtectedRoute>
  );
}
