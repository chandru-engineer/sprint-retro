"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { ReactionSummary } from "@/lib/types";

const AVAILABLE_EMOJIS = ["👍", "❤️", "🎉", "👏", "💡", "🙌"];

export default function ReactionBar({
  retroId,
  userId,
  questionKey,
  reactions,
  onChange,
}: {
  retroId: string;
  userId: number;
  questionKey: string;
  reactions: ReactionSummary[];
  onChange: (reactions: ReactionSummary[]) => void;
}) {
  const [busyEmoji, setBusyEmoji] = useState<string | null>(null);
  const byEmoji = new Map(reactions.map((r) => [r.emoji, r]));

  async function toggle(emoji: string) {
    if (busyEmoji) return;
    setBusyEmoji(emoji);
    try {
      const result = await api.post<{ reactions: Record<string, ReactionSummary[]> }>(
        `/api/retros/${retroId}/feedback/${userId}/react`,
        { emoji, question_key: questionKey }
      );
      onChange(result.reactions[questionKey] || []);
    } catch {
      // Silently ignore — reactions are a light-touch feature, not worth an alert.
    } finally {
      setBusyEmoji(null);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="React to this response">
      {AVAILABLE_EMOJIS.map((emoji) => {
        const entry = byEmoji.get(emoji);
        const active = !!entry?.reacted_by_me;
        return (
          <button
            key={emoji}
            type="button"
            disabled={busyEmoji !== null}
            onClick={() => toggle(emoji)}
            aria-pressed={active}
            aria-label={`React with ${emoji}`}
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-sm transition-colors duration-200 ease-emphasized disabled:opacity-60 ${
              active
                ? "bg-md-primary-container text-md-on-primary-container"
                : "bg-md-surface-container-low text-slate-500 hover:bg-slate-200"
            }`}
          >
            <span>{emoji}</span>
            {entry && entry.count > 0 && <span className="text-xs font-medium">{entry.count}</span>}
          </button>
        );
      })}
    </div>
  );
}
