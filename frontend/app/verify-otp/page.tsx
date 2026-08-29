"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { OrgOption } from "@/lib/types";
import AuthBackground from "@/components/AuthBackground";

const RESEND_COOLDOWN_SECONDS = 30;

function OrgPicker({ pendingToken, orgs, next }: { pendingToken: string; orgs: OrgOption[]; next: string }) {
  const { selectOrg } = useAuth();
  const router = useRouter();
  const [error, setError] = useState("");
  const [busyOrgId, setBusyOrgId] = useState<number | null>(null);

  async function pick(orgId: number) {
    setError("");
    setBusyOrgId(orgId);
    try {
      await selectOrg(pendingToken, orgId);
      router.replace(next || "/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not enter that organization.");
      setBusyOrgId(null);
    }
  }

  return (
    <div className="w-full max-w-sm">
      <div className="flex flex-col items-center mb-7">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/logo.svg" alt="Sprint Retro" className="h-14 w-auto mb-3 drop-shadow-sm" />
        <h1 className="text-2xl font-bold text-slate-900 text-center tracking-tight">Choose an organization</h1>
        <p className="text-sm text-slate-500 text-center mt-1">You belong to more than one. Which one today?</p>
      </div>

      <div className="auth-card rounded-3xl p-6 space-y-2">
        {error && (
          <div className="alert alert-error" role="alert" aria-live="polite">
            {error}
          </div>
        )}
        {orgs.map((org) => (
          <button
            key={org.id}
            type="button"
            disabled={busyOrgId !== null}
            onClick={() => pick(org.id)}
            className="w-full flex items-center justify-between rounded-full px-5 py-3 bg-md-surface-container-low hover:bg-md-surface-container-high transition-colors duration-300 ease-emphasized disabled:opacity-60"
          >
            <span className="font-medium text-slate-900">{org.name}</span>
            <span className="text-xs text-slate-500 capitalize">{busyOrgId === org.id ? "Entering..." : org.role}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function VerifyOtpForm() {
  const { user, loading, verifyOtp } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const emailFromQuery = searchParams.get("email") || "";
  const next = searchParams.get("next") || "";

  const [email, setEmail] = useState(emailFromQuery);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(emailFromQuery ? "We sent a 6-digit code to your email." : "");
  const [submitting, setSubmitting] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [orgChoice, setOrgChoice] = useState<{ pendingToken: string; orgs: OrgOption[] } | null>(null);

  useEffect(() => {
    if (!loading && user) router.replace(next || "/dashboard");
  }, [user, loading, router, next]);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setTimeout(() => setResendCooldown((s) => s - 1), 1000);
    return () => clearTimeout(timer);
  }, [resendCooldown]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await verifyOtp(email, code);
      if (result.requiresOrgSelection) {
        setOrgChoice({ pendingToken: result.pendingToken, orgs: result.orgs });
      } else {
        router.replace(next || "/dashboard");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not verify that code.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    if (!email || resendCooldown > 0) return;
    setError("");
    setNotice("");
    try {
      await api.post("/api/auth/resend-otp", { email });
      setNotice("A new code has been sent.");
      setResendCooldown(RESEND_COOLDOWN_SECONDS);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not resend the code.");
    }
  }

  if (orgChoice) {
    return <OrgPicker pendingToken={orgChoice.pendingToken} orgs={orgChoice.orgs} next={next} />;
  }

  return (
    <div className="w-full max-w-sm">
      <div className="flex flex-col items-center mb-7">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/logo.svg" alt="Sprint Retro" className="h-14 w-auto mb-3 drop-shadow-sm" />
        <h1 className="text-2xl font-bold text-slate-900 text-center tracking-tight">Enter your code</h1>
        <p className="text-sm text-slate-500 text-center mt-1">Check your email for a 6-digit sign-in code.</p>
      </div>

      <form onSubmit={handleSubmit} className="auth-card rounded-3xl p-6 space-y-4">
        {error && (
          <div className="alert alert-error" role="alert" aria-live="polite">
            {error}
          </div>
        )}
        {notice && (
          <div className="alert alert-info" role="status" aria-live="polite">
            {notice}
          </div>
        )}
        <div>
          <label className="label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="username"
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />
        </div>
        <div>
          <label className="label" htmlFor="code">
            6-digit code
          </label>
          <input
            id="code"
            required
            inputMode="numeric"
            pattern="[0-9]{6}"
            maxLength={6}
            autoComplete="one-time-code"
            autoFocus
            className="input text-center text-2xl tracking-[0.5em] font-semibold"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            placeholder="000000"
          />
        </div>
        <button type="submit" disabled={submitting || code.length !== 6} className="btn btn-primary w-full">
          {submitting ? "Verifying..." : "Verify & continue"}
        </button>
        <button
          type="button"
          onClick={handleResend}
          disabled={resendCooldown > 0}
          className="btn btn-secondary w-full"
        >
          {resendCooldown > 0 ? `Resend code (${resendCooldown}s)` : "Resend code"}
        </button>
      </form>
    </div>
  );
}

export default function VerifyOtpPage() {
  return (
    <AuthBackground>
      <Suspense fallback={null}>
        <VerifyOtpForm />
      </Suspense>
    </AuthBackground>
  );
}
