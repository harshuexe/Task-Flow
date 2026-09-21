"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, type User } from "./api";

type AuthValue = {
  token: string | null;
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
};
const AuthContext = createContext<AuthValue | undefined>(undefined);
const publicRoutes = ["/login"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("access_token");
    if (!stored) {
      setLoading(false);
      if (!publicRoutes.includes(pathname)) router.replace("/login");
      return;
    }
    setToken(stored);
    void api.me().then(setUser).catch(() => {
      localStorage.removeItem("access_token");
      setToken(null);
      setUser(null);
      if (!publicRoutes.includes(pathname)) router.replace("/login");
    }).finally(() => setLoading(false));
  }, [pathname, router]);

  useEffect(() => {
    if (!loading && user && publicRoutes.includes(pathname)) router.replace("/");
  }, [loading, pathname, router, user]);

  const value = useMemo<AuthValue>(() => ({
    token, user, loading,
    async login(username, password) {
      const response = await api.login(username, password);
      localStorage.setItem("access_token", response.access_token);
      setToken(response.access_token);
      setUser(await api.me());
      router.replace("/");
    },
    logout() {
      localStorage.removeItem("access_token");
      setToken(null); setUser(null);
      router.replace("/login");
    },
  }), [loading, router, token, user]);

  if (loading && !publicRoutes.includes(pathname)) {
    return <div className="flex min-h-screen items-center justify-center text-slate-500">Loading your workspace...</div>;
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
