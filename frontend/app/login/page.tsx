"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";
import AuthBackground from "@/components/AuthBackground";

function LoginForm() {
  const { user, loading, requestOtp } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "";

  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace(next || "/dashboard");
  }, [user, loading, router, next]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await requestOtp(email);
      const params = new URLSearchParams({ email });
      if (next) params.set("next", next);
      router.push(`/verify-otp?${params.toString()}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send a code. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-sm">
      <div className="flex flex-col items-center mb-7">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/logo.svg" alt="Sprint Retro" className="h-14 w-auto mb-3 drop-shadow-sm" />
        <h1 className="text-2xl font-bold text-slate-900 text-center tracking-tight">Sprint Retro</h1>
        <p className="text-sm text-slate-500 text-center mt-1">
          No password &mdash; we'll email you a one-time code.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="auth-card rounded-3xl p-6 space-y-4">
        {error && (
          <div className="alert alert-error" role="alert" aria-live="polite">
            {error}
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
            autoFocus
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />
        </div>
        <button type="submit" disabled={submitting} className="btn btn-primary w-full">
          {submitting ? "Sending code..." : "Send sign-in code"}
        </button>
      </form>

      <p className="text-center text-sm text-slate-500 mt-5">
        New here?{" "}
        <Link href="/signup" className="font-medium text-md-primary hover:underline">
          Create an organization
        </Link>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <AuthBackground>
      <Suspense fallback={null}>
        <LoginForm />
      </Suspense>
    </AuthBackground>
  );
}
