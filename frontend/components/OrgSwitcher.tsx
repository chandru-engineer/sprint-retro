"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { api, getCurrentOrgId } from "@/lib/api";
import { OrgOption } from "@/lib/types";

export default function OrgSwitcher({ className = "" }: { className?: string }) {
  const { switchOrg } = useAuth();
  const [orgs, setOrgs] = useState<OrgOption[]>([]);
  const [currentOrgId, setCurrentOrgId] = useState("");
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    api
      .get<OrgOption[]>("/api/auth/my-orgs")
      .then((list) => {
        setOrgs(list);
        setCurrentOrgId(String(getCurrentOrgId() ?? list[0]?.id ?? ""));
      })
      .catch(() => {});
  }, []);

  if (orgs.length < 2) return null;

  async function handleChange(orgId: string) {
    setCurrentOrgId(orgId);
    setSwitching(true);
    try {
      await switchOrg(Number(orgId));
      window.location.assign("/dashboard");
    } catch {
      setSwitching(false);
    }
  }

  return (
    <select
      className={`input !min-h-0 !py-1.5 !text-xs w-auto ${className}`}
      value={currentOrgId}
      disabled={switching}
      onChange={(e) => handleChange(e.target.value)}
      aria-label="Switch organization"
    >
      {orgs.map((org) => (
        <option key={org.id} value={org.id}>
          {org.name}
        </option>
      ))}
    </select>
  );
}
