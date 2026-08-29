"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import ProtectedRoute from "@/components/ProtectedRoute";
import StatusBadge from "@/components/StatusBadge";
import SprintHeroResults from "@/components/SprintHeroResults";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { Feedback, Project, RetroDetail, Team } from "@/lib/types";

const QUESTIONS: { key: keyof Feedback; label: string }[] = [
  { key: "achievement", label: "Achievements" },
  { key: "went_well", label: "What Went Well" },
  { key: "did_not_go_well", label: "What Didn't Go Well" },
  { key: "learnings", label: "New Learnings" },
  { key: "improvements", label: "Improvements" },
];

function PmoView({
  retro,
  projectName,
  teamName,
  onRefresh,
}: {
  retro: RetroDetail;
  projectName: string;
  teamName: string;
  onRefresh: () => void;
}) {
  const { user } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function sendInvites() {
    setBusy(true);
    setError("");
    try {
      await api.post(`/api/retros/${retro.id}/invite`);
      onRefresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to send invitations.");
    } finally {
      setBusy(false);
    }
  }

  async function closeRetro() {
    if (!confirm("Mark this retrospective as Completed? Responses will become read-only.")) return;
    setBusy(true);
    setError("");
    try {
      await api.post(`/api/retros/${retro.id}/close`);
      onRefresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to close retrospective.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {error && <div className="alert alert-error">{error}</div>}

      {retro.status === "draft" && (
        <div className="alert alert-info">
          This retro hasn't been sent to the team yet. Click <strong>Notify Team</strong> below to email all invited
          members and open it for responses.
        </div>
      )}

      <div className="card">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2.5 text-sm">
          <div>
            <span className="text-slate-500">Project:</span> <span className="font-medium">{projectName}</span>
          </div>
          <div>
            <span className="text-slate-500">Team:</span> <span className="font-medium">{teamName}</span>
          </div>
          <div>
            <span className="text-slate-500">Sprint:</span> <span className="font-medium">{retro.sprint_name}</span>
          </div>
          <div>
            <span className="text-slate-500">Status:</span> <StatusBadge status={retro.status} />
          </div>
          <div>
            <span className="text-slate-500">Retro Meeting:</span>{" "}
            <span className="font-medium">
              {retro.retro_date}, {retro.retro_time}
            </span>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="font-semibold text-slate-900 mb-2">Participation</h2>
        <div className="flex items-center gap-4 flex-wrap">
          <div className="text-2xl font-bold text-slate-900">
            {retro.submitted_count} / {retro.total_count} Submitted
          </div>
          <div className="text-lg text-brand-600 font-semibold">{retro.completion_percent}%</div>
        </div>
        <div className="mt-4 divide-y divide-slate-100 border border-slate-100 rounded-lg">
          {retro.participants.map((p) => (
            <div key={p.id} className="flex items-center justify-between gap-2 px-3 py-2.5 text-sm">
              <span className="truncate">{p.user_name}</span>
              <StatusBadge status={p.feedback_status === "not_started" ? "pending" : p.feedback_status} />
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:flex-wrap gap-3">
        {retro.status === "draft" && (
          <button className="btn btn-primary" disabled={busy} onClick={sendInvites}>
            Notify Team
          </button>
        )}
        <Link href={`/retros/${retro.id}/responses`} className="btn btn-secondary">
          Review Responses
        </Link>
        <Link href={`/retros/${retro.id}/report`} className="btn btn-secondary">
          View Report
        </Link>
        {retro.status !== "completed" && (
          <button className="btn btn-secondary" disabled={busy} onClick={closeRetro}>
            Mark Completed
          </button>
        )}
      </div>

      {user?.role === "admin" && <SprintHeroResults retroId={retro.id} />}
    </div>
  );
}

function MemberView({ retro }: { retro: RetroDetail }) {
  const { user } = useAuth();
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Feedback | null>(`/api/retros/${retro.id}/feedback/me`)
      .then(setFeedback)
      .finally(() => setLoading(false));
  }, [retro.id]);

  const submitted = feedback?.status === "submitted";

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2.5 text-sm">
          <div>
            <span className="text-slate-500">Sprint:</span> <span className="font-medium">{retro.sprint_name}</span>
          </div>
          <div>
            <span className="text-slate-500">Status:</span> <StatusBadge status={retro.status} />
          </div>
          <div>
            <span className="text-slate-500">Retro Meeting:</span>{" "}
            <span className="font-medium">
              {retro.retro_date}, {retro.retro_time}
            </span>
          </div>
        </div>
      </div>

      {!loading && (
        <div className="card">
          {submitted ? (
            <div className="space-y-4">
              <p className="text-sm text-green-700 font-medium">Response submitted successfully.</p>
              {QUESTIONS.map((q) => (
                <div key={q.key}>
                  <h3 className="text-sm font-semibold text-slate-700">{q.label}</h3>
                  <p className="text-sm text-slate-600 whitespace-pre-wrap mt-1">{feedback?.[q.key] as string}</p>
                </div>
              ))}
              <Link href={`/retros/${retro.id}/responses`} className="btn btn-secondary">
                See Everyone's Responses
              </Link>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <p className="text-sm text-slate-600">
                {feedback?.status === "draft"
                  ? "You have a saved draft. Continue editing your response."
                  : "You haven't started your response yet."}
              </p>
              <Link href={`/retros/${retro.id}/form`} className="btn btn-primary">
                {feedback?.status === "draft" ? "Continue Draft" : "Fill Retrospective"}
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RetroDetailContent() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const [retro, setRetro] = useState<RetroDetail | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [team, setTeam] = useState<Team | null>(null);
  const [error, setError] = useState("");

  function load() {
    api
      .get<RetroDetail>(`/api/retros/${params.id}`)
      .then((r) => {
        setRetro(r);
        if (user?.role !== "member") {
          api.get<Project>(`/api/projects/${r.project_id}`).then(setProject).catch(() => {});
          api.get<Team>(`/api/teams/${r.team_id}`).then(setTeam).catch(() => {});
        }
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load retrospective."));
  }

  useEffect(load, [params.id]);

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!retro) return <p className="text-sm text-slate-500">Loading...</p>;

  return (
    <div>
      <h1 className="page-title mb-6">{retro.sprint_name} Retrospective</h1>
      {user?.role === "member" ? (
        <MemberView retro={retro} />
      ) : (
        <PmoView
          retro={retro}
          projectName={project?.name || `#${retro.project_id}`}
          teamName={team?.name || `#${retro.team_id}`}
          onRefresh={load}
        />
      )}
    </div>
  );
}

export default function RetroDetailPage() {
  return (
    <ProtectedRoute>
      <div className="page">
        <RetroDetailContent />
      </div>
    </ProtectedRoute>
  );
}
