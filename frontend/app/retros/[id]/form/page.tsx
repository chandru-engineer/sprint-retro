"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import ProtectedRoute from "@/components/ProtectedRoute";
import SprintHeroVote from "@/components/SprintHeroVote";
import { api, ApiError } from "@/lib/api";
import { Feedback, FeedbackForm, RetroDetail } from "@/lib/types";

const QUESTIONS: { key: keyof FeedbackForm; title: string; question: string; placeholder: string }[] = [
  {
    key: "achievement",
    title: "1. Achievements",
    question: "What did you achieve during this sprint?",
    placeholder: "Describe your key achievements during this sprint...",
  },
  {
    key: "went_well",
    title: "2. What Went Well",
    question: "What went well during this sprint?",
    placeholder: "What worked well during this sprint?",
  },
  {
    key: "did_not_go_well",
    title: "3. What Didn't Go Well",
    question: "What didn't go well during this sprint?",
    placeholder: "What problems, blockers, or challenges did you face?",
  },
  {
    key: "learnings",
    title: "4. New Learnings",
    question: "What did you learn during this sprint?",
    placeholder: "What new technical, process, or business knowledge did you gain?",
  },
  {
    key: "improvements",
    title: "5. Improvements",
    question: "How can we improve in the next sprint?",
    placeholder: "What should the team improve in the next sprint?",
  },
];

const EMPTY: FeedbackForm = {
  achievement: "",
  went_well: "",
  did_not_go_well: "",
  learnings: "",
  improvements: "",
};

function RetroFormContent() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [retro, setRetro] = useState<RetroDetail | null>(null);
  const [form, setForm] = useState<FeedbackForm>(EMPTY);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get<RetroDetail>(`/api/retros/${params.id}`),
      api.get<Feedback | null>(`/api/retros/${params.id}/feedback/me`),
    ])
      .then(([r, fb]) => {
        setRetro(r);
        if (fb) {
          setForm({
            achievement: fb.achievement,
            went_well: fb.went_well,
            did_not_go_well: fb.did_not_go_well,
            learnings: fb.learnings,
            improvements: fb.improvements,
          });
          setSubmitted(fb.status === "submitted");
        }
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load retrospective."))
      .finally(() => setLoading(false));
  }, [params.id]);

  const answeredCount = Object.values(form).filter((v) => v.trim()).length;

  function update(key: keyof FeedbackForm, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function saveDraft() {
    setSaving(true);
    setError("");
    setNotice("");
    try {
      await api.put(`/api/retros/${params.id}/feedback/draft`, form);
      setNotice("Draft saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save draft.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    try {
      await api.post(`/api/retros/${params.id}/feedback/submit`, form);
      setSubmitted(true);
      setNotice("Response submitted successfully.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit response.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="text-sm text-slate-500">Loading...</p>;
  if (error && !retro) return <p className="text-sm text-red-600">{error}</p>;
  if (!retro) return null;

  if (submitted) {
    return (
      <div className="space-y-4">
        <div className="card space-y-4">
          <p className="text-sm text-green-700 font-medium">Response submitted successfully.</p>
          {QUESTIONS.map((q) => (
            <div key={q.key}>
              <h3 className="text-sm font-semibold text-slate-700">{q.title}</h3>
              <p className="text-sm text-slate-600 whitespace-pre-wrap mt-1">{form[q.key]}</p>
            </div>
          ))}
          <button className="btn btn-secondary" onClick={() => router.push(`/retros/${params.id}`)}>
            Back to Retro
          </button>
        </div>

        <SprintHeroVote retroId={params.id} disabled={retro.status === "completed"} />
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">{retro.sprint_name} Retrospective</h1>
      <div className="flex items-center gap-1 my-3">
        {QUESTIONS.map((q) => (
          <span
            key={q.key}
            className={`h-2 w-8 rounded-full ${form[q.key].trim() ? "bg-brand-600" : "bg-slate-200"}`}
          />
        ))}
        <span className="text-xs text-slate-400 ml-2">{answeredCount} / 5 answered</span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <div className="alert alert-error">{error}</div>}
        {notice && <div className="alert alert-success">{notice}</div>}

        {QUESTIONS.map((q) => (
          <div key={q.key} className="card">
            <h2 className="font-semibold text-slate-900">{q.title}</h2>
            <p className="text-sm text-slate-500 mb-2">{q.question}</p>
            <textarea
              className="input min-h-[120px]"
              placeholder={q.placeholder}
              value={form[q.key]}
              onChange={(e) => update(q.key, e.target.value)}
            />
          </div>
        ))}

        <SprintHeroVote retroId={params.id} disabled={retro.status === "completed"} />

        <div className="flex flex-col-reverse sm:flex-row gap-3 pb-2">
          <button type="button" className="btn btn-secondary w-full sm:w-auto" disabled={saving} onClick={saveDraft}>
            Save Draft
          </button>
          <button type="submit" className="btn btn-primary w-full sm:w-auto" disabled={saving}>
            Submit Response
          </button>
        </div>
      </form>
    </div>
  );
}

export default function RetroFormPage() {
  return (
    <ProtectedRoute>
      <div className="page">
        <RetroFormContent />
      </div>
    </ProtectedRoute>
  );
}
