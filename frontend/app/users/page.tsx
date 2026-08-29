"use client";

import { FormEvent, useEffect, useState } from "react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { api, ApiError } from "@/lib/api";
import { User, UserRole } from "@/lib/types";

function UserForm({ onCreated }: { onCreated: (u: User) => void }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<UserRole>("member");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const user = await api.post<User>("/api/users", { name, email, role });
      onCreated(user);
      setName("");
      setEmail("");
      setRole("member");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create user.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card space-y-3">
      <h2 className="font-semibold text-slate-900">Add User</h2>
      <p className="text-sm text-slate-500 -mt-2">
        There's no password to set &mdash; they'll sign in with a one-time code emailed to them. If this email
        already has a Sprint Retro account elsewhere, they're simply added to your organization.
      </p>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <input required className="input" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
        <input
          required
          type="email"
          className="input"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <select className="input" value={role} onChange={(e) => setRole(e.target.value as UserRole)}>
          <option value="member">Team Member</option>
          <option value="pmo">PMO / Team Lead</option>
          <option value="admin">Admin</option>
        </select>
      </div>
      <button type="submit" disabled={submitting} className="btn btn-primary">
        {submitting ? "Adding..." : "Add User"}
      </button>
    </form>
  );
}

function UsersContent() {
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState("");

  function load() {
    api.get<User[]>("/api/users").then(setUsers).catch(() => setError("Could not load users."));
  }

  useEffect(load, []);

  async function toggleActive(user: User) {
    const action = user.is_active ? "disable" : "enable";
    await api.post(`/api/users/${user.id}/${action}`);
    load();
  }

  return (
    <div className="space-y-6">
      <h1 className="page-title">Users</h1>
      <UserForm onCreated={load} />
      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* Mobile: card list */}
      <div className="grid gap-3 md:hidden">
        {users.map((u) => (
          <div key={u.id} className="row-card">
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="font-semibold text-slate-900">{u.name}</div>
                <div className="text-sm text-slate-500">{u.email}</div>
              </div>
              <span className={`badge ${u.is_active ? "badge-submitted" : "badge-draft"}`}>
                {u.is_active ? "Active" : "Disabled"}
              </span>
            </div>
            <div className="flex items-center justify-between mt-3">
              <span className="text-xs uppercase tracking-wide text-slate-400 font-semibold">{u.role}</span>
              <button className="btn btn-secondary btn-sm" onClick={() => toggleActive(u)}>
                {u.is_active ? "Disable" : "Enable"}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Desktop: table */}
      <div className="data-table-wrap hidden md:block">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td>{u.email}</td>
                <td className="capitalize">{u.role}</td>
                <td>
                  <span className={`badge ${u.is_active ? "badge-submitted" : "badge-draft"}`}>
                    {u.is_active ? "Active" : "Disabled"}
                  </span>
                </td>
                <td className="text-right">
                  <button className="btn btn-secondary btn-sm" onClick={() => toggleActive(u)}>
                    {u.is_active ? "Disable" : "Enable"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function UsersPage() {
  return (
    <ProtectedRoute allow={["admin"]}>
      <div className="page">
        <UsersContent />
      </div>
    </ProtectedRoute>
  );
}
