"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
}

interface AuthContextType {
  token: string | null;
  user: User | null;
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, fullName: string, password: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("access_token");
    if (saved) {
      setToken(saved);
      fetch("http://localhost:8000/auth/me", {
        headers: { Authorization: `Bearer ${saved}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error();
          return res.json();
        })
        .then((data) => setUser(data))
        .catch(() => localStorage.removeItem("access_token"));
    }
  }, []);

  async function login(email: string, password: string) {
    const res = await fetch("http://localhost:8000/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Login failed");
    }
    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    setToken(data.access_token);

    const meRes = await fetch("http://localhost:8000/auth/me", {
      headers: { Authorization: `Bearer ${data.access_token}` },
    });
    if (!meRes.ok) throw new Error("Failed to fetch user");
    const me = await meRes.json();
    setUser(me);
    return me;
  }

  async function register(email: string, fullName: string, password: string) {
    const res = await fetch("http://localhost:8000/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, full_name: fullName, password }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Registration failed");
    }
    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    setToken(data.access_token);

    const meRes = await fetch("http://localhost:8000/auth/me", {
      headers: { Authorization: `Bearer ${data.access_token}` },
    });
    if (!meRes.ok) throw new Error("Failed to fetch user");
    const me = await meRes.json();
    setUser(me);
    return me;
  }

  function logout() {
    localStorage.removeItem("access_token");
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
