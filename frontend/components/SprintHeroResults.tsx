"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { CredIssuerConfig, HeroVoteResults, IssuedCredential } from "@/lib/types";

export default function SprintHeroResults({ retroId }: { retroId: number }) {
  const [results, setResults] = useState<HeroVoteResults | null>(null);
  const [error, setError] = useState("");
  const [credConfig, setCredConfig] = useState<CredIssuerConfig | null>(null);
  const [issuedUserIds, setIssuedUserIds] = useState<Set<number>>(new Set());
  const [issuing, setIssuing] = useState(false);
  const [toast, setToast] = useState("");

  useEffect(() => {
    api
      .get<HeroVoteResults>(`/api/retros/${retroId}/hero-vote/results`)
      .then(setResults)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load Sprint Hero results."));
    api.get<CredIssuerConfig>("/api/credissuer/config").then(setCredConfig).catch(() => {});
    api
      .get<IssuedCredential[]>(`/api/credissuer/history?retro_id=${retroId}`)
      .then((records) => setIssuedUserIds(new Set(records.map((r) => r.user_id))))
      .catch(() => {});
  }, [retroId]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 4000);
    return () => clearTimeout(timer);
  }, [toast]);

  const winner = results && results.total_votes > 0 ? results.results[0] : null;
  const heroCredentialIssued = winner ? issuedUserIds.has(winner.user_id) : false;

  async function issueHeroCredential() {
    if (!winner) return;
    setIssuing(true);
    setError("");
    try {
      await api.post("/api/credissuer/issue", { user_id: winner.user_id, retro_id: retroId });
      setIssuedUserIds((prev) => new Set(prev).add(winner.user_id));
      setToast(`Credential issued to ${winner.user_name}, the Sprint Hero.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not issue the Sprint Hero credential.");
    } finally {
      setIssuing(false);
    }
  }

  return (
    <div className="card">
      {toast && (
        <div className="fixed top-4 right-4 z-50 rounded-2xl bg-md-primary text-white px-4 py-3 text-sm font-medium shadow-lg animate-[fadeIn_0.2s_ease-out]">
          🎖️ {toast}
        </div>
      )}
      <div className="flex items-center justify-between gap-2 mb-1">
        <h2 className="font-semibold text-slate-900">Sprint Hero Results</h2>
        <span className="badge badge-draft">Admin only</span>
      </div>
      <p className="text-sm text-slate-500 mb-4">
        Vote counts, any names voters chose to reveal, and their optional comments.
      </p>

      {error && <div className="alert alert-error mb-3">{error}</div>}

      {!error && !results && <p className="text-sm text-slate-400">Loading...</p>}

      {results && results.total_votes === 0 && (
        <p className="text-sm text-slate-400">No votes cast yet.</p>
      )}

      {results && results.total_votes > 0 && (
        <div className="space-y-2.5">
          {results.results.map((r, i) => {
            const visibleEntries = r.entries.filter((e) => e.voter_name || e.comment);
            return (
              <div
                key={r.user_id}
                className={`rounded-lg px-3.5 py-3 ${i === 0 ? "bg-md-primary-container" : "bg-md-surface-container-low"}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex items-start gap-2">
                    {i === 0 && (
                      <svg
                        aria-hidden="true"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                        className="shrink-0 mt-0.5 text-md-on-primary-container"
                      >
                        <path d="M12 2l2.6 6.6L21 9l-5 4.6L17.4 21 12 17.3 6.6 21 8 13.6 3 9l6.4-.4L12 2Z" />
                      </svg>
                    )}
                    <div
                      className={`font-medium truncate ${i === 0 ? "text-md-on-primary-container" : "text-slate-900"}`}
                    >
                      {r.user_name}
                    </div>
                  </div>
                  <span className="badge badge-open shrink-0">
                    {r.vote_count} {r.vote_count === 1 ? "vote" : "votes"}
                  </span>
                </div>

                {visibleEntries.length > 0 && (
                  <ul className="mt-2 space-y-1.5">
                    {visibleEntries.map((e, idx) => (
                      <li
                        key={idx}
                        className={`text-xs pl-2 border-l-2 ${
                          i === 0
                            ? "border-md-on-primary-container/30 text-md-on-primary-container/90"
                            : "border-slate-300 text-slate-600"
                        }`}
                      >
                        <span className="font-medium">{e.voter_name || "Anonymous"}</span>
                        {e.comment && <span>: {e.comment}</span>}
                      </li>
                    ))}
                  </ul>
                )}

                {i === 0 && credConfig?.configured && (
                  <div className="mt-3 pt-3 border-t border-md-on-primary-container/15">
                    {heroCredentialIssued ? (
                      <span className="badge badge-submitted">Credential Issued</span>
                    ) : (
                      <button
                        className="btn btn-secondary btn-sm !py-1 !px-2.5 !text-xs"
                        disabled={issuing}
                        onClick={issueHeroCredential}
                      >
                        {issuing ? "Issuing..." : "Issue Credential to Sprint Hero"}
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
          <p className="text-xs text-slate-400 pt-1">{results.total_votes} total votes cast.</p>
        </div>
      )}

      {winner && !credConfig?.configured && (
        <p className="text-xs text-slate-400 pt-2">
          Connect CredIssuer in{" "}
          <Link href="/settings" className="text-md-primary hover:underline">
            Settings
          </Link>{" "}
          to issue a credential to the Sprint Hero.
        </p>
      )}
    </div>
  );
}
