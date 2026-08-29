"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { UserRole } from "@/lib/types";

export default function ProtectedRoute({
  children,
  allow,
}: {
  children: React.ReactNode;
  allow?: UserRole[];
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    if (allow && !allow.includes(user.role)) {
      router.replace("/dashboard");
    }
  }, [user, loading, allow, router, pathname]);

  if (loading || !user || (allow && !allow.includes(user.role))) {
    return <div className="page text-slate-500 text-sm">Loading...</div>;
  }

  return <>{children}</>;
}
