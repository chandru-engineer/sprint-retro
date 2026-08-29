"use client";

import { FormEvent, useEffect, useState } from "react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { api, ApiError } from "@/lib/api";
import { CredIssuerConfig, CredIssuerTemplate } from "@/lib/types";

function CredIssuerCard() {
  const [config, setConfig] = useState<CredIssuerConfig | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [templates, setTemplates] = useState<CredIssuerTemplate[]>([]);
  const [templateId, setTemplateId] = useState("");
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  function load() {
    api.get<CredIssuerConfig>("/api/credissuer/config").then(setConfig).catch(() => {});
  }

  useEffect(load, []);

  async function loadTemplates() {
    setError("");
    setNotice("");
    if (!apiKey.trim()) {
      setError("Enter an API key first.");
      return;
    }
    setLoadingTemplates(true);
    try {
      const list = await api.get<CredIssuerTemplate[]>(
        `/api/credissuer/templates?api_key=${encodeURIComponent(apiKey.trim())}`
      );
      setTemplates(list);
      setTemplateId(list[0]?.id || "");
      setNotice(`Connected — ${list.length} template(s) available.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach CredIssuer with that key.");
      setTemplates([]);
    } finally {
      setLoadingTemplates(false);
    }
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    setError("");
    setNotice("");
    const chosen = templates.find((t) => t.id === templateId);
    if (!chosen) {
      setError("Load templates and pick one first.");
      return;
    }
    setSaving(true);
    try {
      const saved = await api.put<CredIssuerConfig>("/api/credissuer/config", {
        api_key: apiKey.trim(),
        template_id: chosen.id,
        template_name: chosen.name,
      });
      setConfig(saved);
      setApiKey("");
      setTemplates([]);
      setNotice("CredIssuer is configured. You can now issue credentials with one click from a retro.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save the CredIssuer configuration.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card space-y-4">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h2 className="font-semibold text-slate-900">CredIssuer Integration</h2>
          <p className="text-sm text-slate-500 mt-1">
            Connect CredIssuer to issue Verifiable Credentials straight from a retro, in one click.
          </p>
        </div>
        <span className="badge badge-mock shrink-0">Mock integration</span>
      </div>

      {config?.configured && (
        <div className="rounded-2xl bg-md-primary-container/40 border border-md-primary/20 px-4 py-3 text-sm">
          <div className="font-medium text-slate-900">Currently configured</div>
          <div className="text-slate-600 mt-0.5">
            Template: <span className="font-medium">{config.template_name}</span> &middot; API key:{" "}
            <span className="font-mono">{config.api_key_masked}</span>
          </div>
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-info">{notice}</div>}

      <form onSubmit={handleSave} className="space-y-3">
        <div>
          <label className="label" htmlFor="credissuer-key">
            {config?.configured ? "New API key (leave blank to keep, or replace to reconfigure)" : "CredIssuer API key"}
          </label>
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              id="credissuer-key"
              className="input"
              type="password"
              placeholder="sk_live_..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              autoComplete="off"
            />
            <button
              type="button"
              className="btn btn-secondary shrink-0"
              disabled={loadingTemplates}
              onClick={loadTemplates}
            >
              {loadingTemplates ? "Connecting..." : "Load Templates"}
            </button>
          </div>
        </div>

        {templates.length > 0 && (
          <div>
            <label className="label" htmlFor="credissuer-template">
              Credential template
            </label>
            <select
              id="credissuer-template"
              className="input"
              value={templateId}
              onChange={(e) => setTemplateId(e.target.value)}
            >
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-slate-500 mt-1.5">
              {templates.find((t) => t.id === templateId)?.description}
            </p>
          </div>
        )}

        <button type="submit" disabled={saving || templates.length === 0} className="btn btn-primary">
          {saving ? "Saving..." : "Save Configuration"}
        </button>
      </form>
    </div>
  );
}

function SettingsContent() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Settings</h1>
        <p className="text-sm text-slate-500 mt-1">Organization-wide integrations and configuration.</p>
      </div>
      <CredIssuerCard />
    </div>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute allow={["admin"]}>
      <div className="page">
        <SettingsContent />
      </div>
    </ProtectedRoute>
  );
}
