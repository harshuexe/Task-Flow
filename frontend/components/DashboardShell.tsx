"use client";

import { usePathname } from "next/navigation";
import { Header } from "./Header";
import { useAuth } from "../lib/auth-context";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, loading } = useAuth();
  const isAuthenticatedDashboard = !loading && Boolean(user) && pathname !== "/login";

  return (
    <>
      {isAuthenticatedDashboard && <Header />}
      <main>{children}</main>
    </>
  );
}
