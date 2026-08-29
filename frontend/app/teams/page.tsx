"use client";

import { FormEvent, useEffect, useState } from "react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { api, ApiError } from "@/lib/api";
import { Team, User } from "@/lib/types";

function TeamForm({ users, onSaved }: { users: User[]; onSaved: () => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [teamLeadId, setTeamLeadId] = useState("");
  const [memberIds, setMemberIds] = useState<Set<number>>(new Set());
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function toggleMember(id: number) {
    setMemberIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await api.post<Team>("/api/teams", {
        name,
        description,
        team_lead_id: teamLeadId ? Number(teamLeadId) : null,
        member_ids: Array.from(memberIds),
      });
      setName("");
      setDescription("");
      setTeamLeadId("");
      setMemberIds(new Set());
      onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create team.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card space-y-3">
      <h2 className="font-semibold text-slate-900">Create Team</h2>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <input required className="input" placeholder="Team name" value={name} onChange={(e) => setName(e.target.value)} />
        <input
          className="input"
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <select className="input" value={teamLeadId} onChange={(e) => setTeamLeadId(e.target.value)}>
          <option value="">Team Lead (optional)</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="label">Members</label>
        <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 max-h-56 overflow-y-auto">
          {users.map((u) => (
            <label key={u.id} className="flex items-center gap-2.5 px-3 py-3 text-sm cursor-pointer active:bg-slate-50">
              <input
                type="checkbox"
                className="h-4 w-4 shrink-0 accent-brand-600"
                checked={memberIds.has(u.id)}
                onChange={() => toggleMember(u.id)}
              />
              <span className="truncate">
                {u.name} <span className="text-slate-400">({u.email})</span>
              </span>
            </label>
          ))}
        </div>
      </div>
      <button type="submit" disabled={submitting} className="btn btn-primary">
        {submitting ? "Creating..." : "Create Team"}
      </button>
    </form>
  );
}

function TeamsContent() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState("");

  function load() {
    api.get<Team[]>("/api/teams").then(setTeams).catch(() => setError("Could not load teams."));
    api.get<User[]>("/api/users").then(setUsers).catch(() => {});
  }

  useEffect(load, []);

  return (
    <div className="space-y-6">
      <h1 className="page-title">Teams</h1>
      <TeamForm users={users} onSaved={load} />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="grid sm:grid-cols-2 gap-4">
        {teams.map((t) => (
          <div key={t.id} className="card">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">{t.name}</h3>
              <span className={`badge ${t.is_active ? "badge-submitted" : "badge-draft"}`}>
                {t.is_active ? "Active" : "Inactive"}
              </span>
            </div>
            {t.description && <p className="text-sm text-slate-500 mt-1">{t.description}</p>}
            <p className="text-xs text-slate-400 mt-3 uppercase tracking-wide">Members</p>
            <ul className="text-sm text-slate-600 mt-1 space-y-0.5">
              {t.members.length === 0 && <li className="text-slate-400">No members</li>}
              {t.members.map((m) => (
                <li key={m.id}>{m.name}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function TeamsPage() {
  return (
    <ProtectedRoute allow={["admin"]}>
      <div className="page">
        <TeamsContent />
      </div>
    </ProtectedRoute>
  );
}
