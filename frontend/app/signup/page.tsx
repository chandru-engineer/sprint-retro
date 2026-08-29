"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import AuthBackground from "@/components/AuthBackground";

export default function SignupPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [orgName, setOrgName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [user, loading, router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.post("/api/auth/signup", { org_name: orgName, name, email });
      router.push(`/verify-otp?email=${encodeURIComponent(email)}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create your account.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthBackground>
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-7">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo.svg" alt="Sprint Retro" className="h-14 w-auto mb-3 drop-shadow-sm" />
          <h1 className="text-2xl font-bold text-slate-900 text-center tracking-tight">Create your organization</h1>
          <p className="text-sm text-slate-500 text-center mt-1">You'll be the Admin. Invite your team afterward.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-card rounded-3xl p-6 space-y-4">
          {error && (
            <div className="alert alert-error" role="alert" aria-live="polite">
              {error}
            </div>
          )}
          <div>
            <label className="label" htmlFor="orgName">
              Organization name
            </label>
            <input
              id="orgName"
              required
              className="input"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="Acme Corp"
            />
          </div>
          <div>
            <label className="label" htmlFor="name">
              Your name
            </label>
            <input
              id="name"
              required
              autoComplete="name"
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Alex Doe"
            />
          </div>
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
          <button type="submit" disabled={submitting} className="btn btn-primary w-full">
            {submitting ? "Creating..." : "Create account"}
          </button>
        </form>

        <p className="text-center text-sm text-slate-500 mt-5">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-md-primary hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </AuthBackground>
  );
}
