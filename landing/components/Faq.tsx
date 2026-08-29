"use client";

import { useState } from "react";

const FAQS = [
  {
    q: "Is this a project management or issue-tracking tool?",
    a: "No. Sprint Retro does one thing: collect, store, and report sprint retrospective feedback. There are no action items, tasks, boards, or issue tracking — that's intentional.",
  },
  {
    q: "Where does our data live?",
    a: "In a single SQLite file on your own server, mounted as a Docker volume. Nothing is sent to a third-party form service.",
  },
  {
    q: "Does it send email invitations?",
    a: "Yes, over SMTP you configure. Invitations only go out when a PMO/Team Lead explicitly clicks Notify Team on a retro.",
  },
  {
    q: "What roles are supported?",
    a: "Three: Admin (users, teams, projects), PMO / Team Lead (retros, invitations, reports), and Team Member (fill and submit their own response).",
  },
  {
    q: "Is there any AI involved?",
    a: "No AI summarization or generation in V1. Reports simply consolidate the actual submitted responses.",
  },
  {
    q: "Can a team member edit their response after submitting?",
    a: "No — once submitted, a response becomes read-only. They can save and edit drafts freely before that.",
  },
];

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`shrink-0 text-md-on-surface-variant transition-transform duration-300 ease-emphasized ${open ? "rotate-180" : ""}`}
      aria-hidden="true"
    >
      <path d="M6 9l6 6 6-6" />
    </svg>
  );
}

export default function Faq() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="mx-auto max-w-3xl px-4 py-20 sm:px-6 sm:py-28">
      <div className="text-center">
        <span className="md-chip">Good to know</span>
        <h2 className="mt-5 text-3xl font-medium tracking-tight text-md-on-background sm:text-4xl">
          Frequently asked questions
        </h2>
      </div>

      <div className="mt-12 space-y-3">
        {FAQS.map((item, i) => {
          const open = openIndex === i;
          return (
            <div
              key={item.q}
              className="overflow-hidden rounded-lg bg-md-surface-container transition-colors duration-300 hover:bg-md-surface-container-high"
            >
              <button
                onClick={() => setOpenIndex(open ? null : i)}
                aria-expanded={open}
                className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
              >
                <span className="text-base font-medium text-md-on-background">{item.q}</span>
                <ChevronIcon open={open} />
              </button>
              <div
                className="grid transition-all duration-300 ease-emphasized"
                style={{ gridTemplateRows: open ? "1fr" : "0fr" }}
              >
                <div className="overflow-hidden">
                  <p className="px-6 pb-5 text-sm leading-relaxed text-md-on-surface-variant">{item.a}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
