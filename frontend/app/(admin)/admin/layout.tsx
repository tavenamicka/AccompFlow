"use client";

import { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/lib/auth";
import { IconChart, IconUsers, IconDocument, IconMail, IconProfile, IconShield, IconLogout } from "@/components/icons";

const NAV = [
  { href: "/admin", label: "Vue d'ensemble", icon: IconChart },
  { href: "/admin/clients", label: "Clients", icon: IconUsers },
  { href: "/admin/documents", label: "Documents", icon: IconDocument },
  { href: "/admin/invitations", label: "Invitations", icon: IconMail },
  { href: "/admin/utilisateurs", label: "Utilisateurs", icon: IconProfile },
];

export function AdminGuard({ children }: { children: ReactNode }) {
  const { user } = useAuth();

  if (!user || (user.role !== "owner" && user.role !== "staff")) {
    return (
      <div className="mx-auto max-w-md p-8 text-center text-sm text-slate-500">
        Cette section est réservée au personnel.
      </div>
    );
  }

  return <>{children}</>;
}

function AdminTopBar() {
  const { user, logout } = useAuth();

  return (
    <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 pb-4 pt-8">
      <div className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand text-white">
          <IconShield width={18} height={18} />
        </span>
        <span className="hidden font-heading text-lg font-bold tracking-tight text-slate-800 sm:inline">
          AccompFlow
        </span>
        <span className="rounded-full bg-brand-accent/15 px-2.5 py-1 font-heading text-[11px] font-bold uppercase tracking-wide text-brand-accent">
          Admin
        </span>
      </div>
      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        <Link
          href="/dashboard"
          className="whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-semibold text-slate-500 transition-colors hover:bg-sand hover:text-brand"
        >
          Mon espace
        </Link>
        {user && (
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-accent/15 font-heading text-sm font-bold text-brand-accent">
            {user.name.charAt(0).toUpperCase()}
          </span>
        )}
        <button
          onClick={logout}
          aria-label="Se déconnecter"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-sand hover:text-brand"
        >
          <IconLogout width={17} height={17} />
        </button>
      </div>
    </header>
  );
}

export default function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <ProtectedRoute>
      <AdminGuard>
        <div className="relative flex min-h-screen flex-col overflow-x-hidden bg-cream">
          <div aria-hidden className="pointer-events-none absolute -right-24 -top-32 h-80 w-80 rounded-full bg-brand-accent/15 blur-3xl" />
          <div aria-hidden className="pointer-events-none absolute -left-20 top-72 h-64 w-64 rounded-full bg-brand-light/20 blur-3xl" />
          <AdminTopBar />
          <div className="relative mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 pb-10 pt-2 md:flex-row">
            <aside className="shrink-0 md:w-52">
              <nav className="flex gap-1 overflow-x-auto rounded-3xl bg-white p-2 shadow-[0_14px_30px_-18px_rgba(60,40,25,0.35)] md:flex-col md:gap-0.5">
                {NAV.map((item) => {
                  const active =
                    item.href === "/admin" ? pathname === item.href : pathname.startsWith(item.href);
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={clsx(
                        "flex shrink-0 items-center gap-2.5 rounded-2xl px-3.5 py-2.5 text-sm font-semibold transition-colors",
                        active ? "bg-brand text-white" : "text-slate-500 hover:bg-sand hover:text-brand"
                      )}
                    >
                      <Icon width={18} height={18} />
                      <span className="whitespace-nowrap">{item.label}</span>
                    </Link>
                  );
                })}
              </nav>
            </aside>
            <main className="min-w-0 flex-1">{children}</main>
          </div>
        </div>
      </AdminGuard>
    </ProtectedRoute>
  );
}
