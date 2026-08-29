"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import ProtectedRoute from "@/components/ProtectedRoute";
import ReactionBar from "@/components/ReactionBar";
import { api, ApiError } from "@/lib/api";
import { FeedbackWithUser, ReactionSummary, RetroDetail } from "@/lib/types";

const QUESTIONS: { key: keyof FeedbackWithUser; label: string }[] = [
  { key: "achievement", label: "Achievements" },
  { key: "went_well", label: "What Went Well" },
  { key: "did_not_go_well", label: "What Didn't Go Well" },
  { key: "learnings", label: "New Learnings" },
  { key: "improvements", label: "Improvements" },
];

function ResponsesContent() {
  const params = useParams<{ id: string }>();
  const [retro, setRetro] = useState<RetroDetail | null>(null);
  const [feedbacks, setFeedbacks] = useState<FeedbackWithUser[]>([]);
  const [error, setError] = useState("");
  const [activeQuestion, setActiveQuestion] = useState(QUESTIONS[0].key);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<RetroDetail>(`/api/retros/${params.id}`),
      api.get<FeedbackWithUser[]>(`/api/retros/${params.id}/feedback`),
    ])
      .then(([r, fb]) => {
        setRetro(r);
        setFeedbacks(fb);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load responses."));
  }, [params.id]);

  const selectedUser = useMemo(
    () => feedbacks.find((f) => f.user_id === selectedUserId) || null,
    [feedbacks, selectedUserId]
  );

  function handleReactionsChange(userId: number, questionKey: string, reactions: ReactionSummary[]) {
    setFeedbacks((prev) =>
      prev.map((fb) =>
        fb.user_id === userId ? { ...fb, reactions: { ...fb.reactions, [questionKey]: reactions } } : fb
      )
    );
  }

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!retro) return <p className="text-sm text-slate-500">Loading...</p>;

  if (selectedUser) {
    return (
      <div>
        <button
          className="text-sm font-medium text-brand-600 hover:underline mb-4 -ml-1 px-1 py-2"
          onClick={() => setSelectedUserId(null)}
        >
          ← Back to all responses
        </button>
        <h1 className="page-title">{selectedUser.user_name}</h1>
        <p className="text-sm text-slate-500 mb-6">{retro.sprint_name}</p>
        <div className="space-y-4">
          {QUESTIONS.map((q) => (
            <div key={q.key} className="card">
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">{q.label}</h2>
              <p className="text-sm text-slate-600 whitespace-pre-wrap mt-2 mb-3">{selectedUser[q.key] as string}</p>
              <ReactionBar
                retroId={params.id}
                userId={selectedUser.user_id}
                questionKey={q.key as string}
                reactions={selectedUser.reactions[q.key as string] || []}
                onChange={(reactions) => handleReactionsChange(selectedUser.user_id, q.key as string, reactions)}
              />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title mb-1">{retro.sprint_name} — Responses</h1>
      <p className="text-sm text-slate-500 mb-6">
        {feedbacks.length} of {retro.total_count} submitted
      </p>

      <div className="flex gap-2 mb-4 overflow-x-auto -mx-1 px-1 pb-1 sm:flex-wrap sm:overflow-visible">
        {QUESTIONS.map((q) => (
          <button
            key={q.key}
            onClick={() => setActiveQuestion(q.key)}
            className={`shrink-0 px-3.5 py-2.5 rounded-full text-sm font-medium transition-colors duration-300 ease-emphasized ${
              activeQuestion === q.key
                ? "bg-md-primary text-white"
                : "bg-md-surface-container-high text-slate-600 hover:bg-slate-200"
            }`}
          >
            {q.label}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {feedbacks.length === 0 && <p className="text-sm text-slate-400">No responses submitted yet.</p>}
        {feedbacks.map((fb) => (
          <div key={fb.id} className="card">
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="font-semibold text-slate-900">{fb.user_name}</span>
              <button
                className="text-xs font-medium text-brand-600 hover:underline shrink-0"
                onClick={() => setSelectedUserId(fb.user_id)}
              >
                View full response
              </button>
            </div>
            <p className="text-sm text-slate-600 whitespace-pre-wrap mb-3">{fb[activeQuestion] as string}</p>
            <ReactionBar
              retroId={params.id}
              userId={fb.user_id}
              questionKey={activeQuestion as string}
              reactions={fb.reactions[activeQuestion as string] || []}
              onChange={(reactions) => handleReactionsChange(fb.user_id, activeQuestion as string, reactions)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ResponsesPage() {
  return (
    <ProtectedRoute allow={["admin", "pmo", "member"]}>
      <div className="page">
        <ResponsesContent />
      </div>
    </ProtectedRoute>
  );
}
