"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ProtectedRoute from "@/components/ProtectedRoute";
import { api, ApiError } from "@/lib/api";
import { Report } from "@/lib/types";

function Section({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mb-6 print:mb-4">
      <h2 className="text-sm font-bold tracking-wide text-slate-900 border-b border-slate-300 pb-1 mb-2">
        {title}
      </h2>
      {items.length === 0 ? (
        <p className="text-sm text-slate-400">No responses.</p>
      ) : (
        <ul className="list-disc list-inside space-y-1">
          {items.map((item, idx) => (
            <li key={idx} className="text-sm text-slate-700">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ReportContent() {
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Report>(`/api/retros/${params.id}/report`)
      .then(setReport)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load report."));
  }, [params.id]);

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!report) return <p className="text-sm text-slate-500">Loading...</p>;

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6 print:hidden">
        <h1 className="page-title">Sprint Retrospective Report</h1>
        <button className="btn btn-secondary" onClick={() => window.print()}>
          Print / Export PDF
        </button>
      </div>

      <div className="card print:border-none print:shadow-none">
        <h1 className="hidden print:block text-lg font-bold text-center mb-4">SPRINT RETROSPECTIVE REPORT</h1>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-1.5 text-sm mb-6">
          <div>
            <span className="text-slate-500">Project:</span> <span className="font-medium">{report.project_name}</span>
          </div>
          <div>
            <span className="text-slate-500">Team:</span> <span className="font-medium">{report.team_name}</span>
          </div>
          <div>
            <span className="text-slate-500">Sprint:</span> <span className="font-medium">{report.sprint_name}</span>
          </div>
          <div>
            <span className="text-slate-500">Sprint Period:</span>{" "}
            <span className="font-medium">
              {report.sprint_start_date} - {report.sprint_end_date}
            </span>
          </div>
          <div>
            <span className="text-slate-500">Retro Meeting:</span>{" "}
            <span className="font-medium">
              {report.retro_date} {report.retro_time}
            </span>
          </div>
          <div>
            <span className="text-slate-500">Participants:</span>{" "}
            <span className="font-medium">{report.participants}</span>
          </div>
          <div>
            <span className="text-slate-500">Responses:</span>{" "}
            <span className="font-medium">
              {report.responses} / {report.participants}
            </span>
          </div>
        </div>

        <Section title="ACHIEVEMENTS" items={report.achievements} />
        <Section title="WHAT WENT WELL" items={report.went_well} />
        <Section title="WHAT DIDN'T GO WELL" items={report.did_not_go_well} />
        <Section title="NEW LEARNINGS" items={report.learnings} />
        <Section title="HOW CAN WE IMPROVE" items={report.improvements} />
      </div>
    </div>
  );
}

export default function ReportPage() {
  return (
    <ProtectedRoute allow={["admin", "pmo"]}>
      <div className="page">
        <ReportContent />
      </div>
    </ProtectedRoute>
  );
}
