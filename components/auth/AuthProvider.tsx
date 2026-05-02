"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { AuthUser } from "@/lib/auth-types";
import { apiClient } from "@/lib/api-client";

type AuthContextValue = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  setUser: (user: AuthUser | null) => void;
  refreshUser: () => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export default function AuthProvider({
  children,
  initialUser,
}: {
  children: React.ReactNode;
  initialUser: AuthUser | null;
}) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(initialUser);

  useEffect(() => {
    setUser(initialUser);
  }, [initialUser]);

  useEffect(() => {
    if (user) {
      localStorage.setItem("smartspend_user", JSON.stringify(user));
    } else {
      localStorage.removeItem("smartspend_user");
    }
  }, [user]);

  useEffect(() => {
    if (initialUser) return;

    const cached = localStorage.getItem("smartspend_user");
    if (cached) {
      try {
        setUser(JSON.parse(cached) as AuthUser);
      } catch {
        localStorage.removeItem("smartspend_user");
      }
    }
  }, [initialUser]);

  useEffect(() => {
    if (initialUser) {
      return;
    }
    let cancelled = false;
    void apiClient
      .getCurrentUser()
      .then((response) => {
        if (!cancelled) {
          setUser(response.data);
        }
      })
      .catch(() => null);

    return () => {
      cancelled = true;
    };
  }, [initialUser]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      setUser,
      refreshUser: async () => {
        try {
          const response = await apiClient.getCurrentUser();
          setUser(response.data);
        } catch {
          setUser(null);
        }
      },
      logout: async () => {
        await apiClient.logout().catch(() => null);
        setUser(null);
        localStorage.removeItem("smartspend_user");
        router.push("/login");
        router.refresh();
      },
    }),
    [router, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return value;
}
