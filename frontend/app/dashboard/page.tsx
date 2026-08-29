"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";

interface PmoDashboard {
  role: "admin" | "pmo";
  active_retros: number;
  pending_responses: number;
  completed_retros: number;
}

interface MemberRetroItem {
  id: number;
  sprint_name: string;
  team_name: string;
  retro_date: string;
  status: string;
  feedback_status: string;
}

interface MemberDashboard {
  role: "member";
  pending_retros: MemberRetroItem[];
  completed_retros: MemberRetroItem[];
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="card">
      <div className="text-3xl sm:text-4xl font-bold text-slate-900 tabular-nums">{value}</div>
      <div className="text-sm text-slate-500 mt-1">{label}</div>
    </div>
  );
}

function MemberRetroCard({ item }: { item: MemberRetroItem }) {
  return (
    <Link
      href={item.feedback_status === "submitted" ? `/retros/${item.id}` : `/retros/${item.id}/form`}
      className="card block transition-all duration-300 ease-emphasized hover:shadow-md hover:scale-[1.01]"
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="font-semibold text-slate-900">{item.sprint_name}</div>
          <div className="text-sm text-slate-500">{item.team_name}</div>
        </div>
        <StatusBadge status={item.feedback_status === "submitted" ? "submitted" : item.status} />
      </div>
      <div className="text-xs text-slate-400 mt-2">Retro meeting: {item.retro_date}</div>
    </Link>
  );
}

function DashboardContent() {
  const { user } = useAuth();
  const [data, setData] = useState<PmoDashboard | MemberDashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<PmoDashboard | MemberDashboard>("/api/dashboard")
      .then(setData)
      .catch(() => setError("Could not load dashboard."));
  }, []);

  if (error) return <div className="text-sm text-red-600">{error}</div>;
  if (!data) return <div className="text-sm text-slate-500">Loading...</div>;

  if (data.role === "member") {
    return (
      <div className="space-y-8">
        <h1 className="page-title">Welcome, {user?.name}</h1>
        <section>
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Pending Retros</h2>
          {data.pending_retros.length === 0 ? (
            <p className="text-sm text-slate-400">Nothing pending. You're all caught up.</p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {data.pending_retros.map((r) => (
                <MemberRetroCard key={r.id} item={r} />
              ))}
            </div>
          )}
        </section>
        <section>
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Completed Retros</h2>
          {data.completed_retros.length === 0 ? (
            <p className="text-sm text-slate-400">No completed retros yet.</p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {data.completed_retros.map((r) => (
                <MemberRetroCard key={r.id} item={r} />
              ))}
            </div>
          )}
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="page-title">Dashboard</h1>
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Active Retros" value={data.active_retros} />
        <StatCard label="Pending Responses" value={data.pending_responses} />
        <StatCard label="Completed Retros" value={data.completed_retros} />
      </div>
      <Link href="/retros" className="btn btn-primary inline-flex">
        View Retrospectives
      </Link>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <div className="page">
        <DashboardContent />
      </div>
    </ProtectedRoute>
  );
}
