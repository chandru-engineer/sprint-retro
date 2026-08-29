"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { HeroCandidate, HeroVote } from "@/lib/types";

const COMMENT_MAX = 500;

export default function SprintHeroVote({ retroId, disabled }: { retroId: string; disabled: boolean }) {
  const [candidates, setCandidates] = useState<HeroCandidate[]>([]);
  const [vote, setVote] = useState<HeroVote | null>(null);
  const [candidateId, setCandidateId] = useState("");
  const [isAnonymous, setIsAnonymous] = useState(true);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    Promise.all([
      api.get<HeroCandidate[]>(`/api/retros/${retroId}/hero-vote/candidates`),
      api.get<HeroVote | null>(`/api/retros/${retroId}/hero-vote/me`),
    ])
      .then(([c, v]) => {
        setCandidates(c);
        setVote(v);
        if (v) {
          setCandidateId(String(v.candidate_id));
          setIsAnonymous(v.is_anonymous);
          setComment(v.comment || "");
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [retroId]);

  async function saveVote() {
    if (!candidateId) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const result = await api.put<HeroVote>(`/api/retros/${retroId}/hero-vote`, {
        candidate_id: Number(candidateId),
        is_anonymous: isAnonymous,
        comment: comment.trim() || null,
      });
      setVote(result);
      setNotice("Your Sprint Hero vote has been saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save your vote.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return null;

  return (
    <div className="card">
      <h2 className="font-semibold text-slate-900">Vote for your Sprint Hero</h2>
      <p className="text-sm text-slate-500 mb-4">
        Recognize anyone across the organization who stood out this sprint &mdash; not just your own team.
      </p>

      {error && <div className="alert alert-error mb-3">{error}</div>}
      {notice && <div className="alert alert-success mb-3">{notice}</div>}

      {disabled ? (
        <div className="text-sm text-slate-600 space-y-1.5">
          {vote ? (
            <>
              <p>
                You voted for <span className="font-medium">{vote.candidate_name}</span>. Voting is now closed.
              </p>
              {vote.comment && <p className="text-slate-500 italic">&ldquo;{vote.comment}&rdquo;</p>}
            </>
          ) : (
            <p>Voting is closed for this retrospective.</p>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <select className="input" value={candidateId} onChange={(e) => setCandidateId(e.target.value)}>
            <option value="">Select a person...</option>
            {candidates.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.email})
              </option>
            ))}
          </select>

          <div>
            <textarea
              className="input min-h-[80px]"
              placeholder="Why are you voting for them? (optional)"
              value={comment}
              maxLength={COMMENT_MAX}
              onChange={(e) => setComment(e.target.value)}
            />
            <div className="text-xs text-slate-400 mt-1 text-right">
              {comment.length}/{COMMENT_MAX}
            </div>
          </div>

          <label className="flex items-center gap-2.5 text-sm text-slate-600 cursor-pointer">
            <input
              type="checkbox"
              className="h-4 w-4 shrink-0 accent-brand-600"
              checked={!isAnonymous}
              onChange={(e) => setIsAnonymous(!e.target.checked)}
            />
            Show my name in the results (otherwise your vote stays anonymous)
          </label>

          <button type="button" className="btn btn-primary btn-sm" disabled={!candidateId || saving} onClick={saveVote}>
            {saving ? "Saving..." : vote ? "Update Vote" : "Save Vote"}
          </button>

          {vote && (
            <p className="text-xs text-slate-400">
              Currently voted for <span className="font-medium text-slate-500">{vote.candidate_name}</span>
              {vote.is_anonymous ? " (anonymously)" : " (your name will be shown)"}.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
