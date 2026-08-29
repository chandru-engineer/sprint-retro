"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { OrgOption, User } from "@/lib/types";

interface TokenResponse {
  requires_org_selection: boolean;
  access_token: string | null;
  user: User | null;
  pending_token: string | null;
  orgs: OrgOption[] | null;
}

type OtpVerifyResult =
  | { requiresOrgSelection: false }
  | { requiresOrgSelection: true; pendingToken: string; orgs: OrgOption[] };

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  requestOtp: (email: string) => Promise<void>;
  verifyOtp: (email: string, code: string) => Promise<OtpVerifyResult>;
  selectOrg: (pendingToken: string, orgId: number) => Promise<void>;
  switchOrg: (orgId: number) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_KEY = "sprint_retro_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get<User>("/api/auth/me")
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
      })
      .finally(() => setLoading(false));
  }, []);

  function applyToken(res: TokenResponse) {
    if (!res.access_token || !res.user) return;
    localStorage.setItem(TOKEN_KEY, res.access_token);
    setUser(res.user);
  }

  async function requestOtp(email: string) {
    await api.post("/api/auth/login", { email });
  }

  async function verifyOtp(email: string, code: string): Promise<OtpVerifyResult> {
    const res = await api.post<TokenResponse>("/api/auth/verify-otp", { email, code });
    if (res.requires_org_selection) {
      return { requiresOrgSelection: true, pendingToken: res.pending_token!, orgs: res.orgs! };
    }
    applyToken(res);
    return { requiresOrgSelection: false };
  }

  async function selectOrg(pendingToken: string, orgId: number) {
    const previousToken = localStorage.getItem(TOKEN_KEY);
    localStorage.setItem(TOKEN_KEY, pendingToken);
    try {
      const res = await api.post<TokenResponse>("/api/auth/select-org", { org_id: orgId });
      applyToken(res);
    } catch (err) {
      if (previousToken) localStorage.setItem(TOKEN_KEY, previousToken);
      else localStorage.removeItem(TOKEN_KEY);
      throw err;
    }
  }

  async function switchOrg(orgId: number) {
    const res = await api.post<TokenResponse>("/api/auth/switch-org", { org_id: orgId });
    applyToken(res);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    router.push("/login");
  }

  return (
    <AuthContext.Provider value={{ user, loading, requestOtp, verifyOtp, selectOrg, switchOrg, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
