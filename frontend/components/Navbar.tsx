"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { useAuth } from "@/lib/auth";
import { Logo } from "@/components/Logo";
import { IconHome, IconRemote, IconDocument, IconProfile, IconShield, IconLogout } from "@/components/icons";

const HOME_LINK = { href: "/dashboard", label: "Accueil", icon: IconHome };
const CLIENT_LINKS = [
  { href: "/dashboard/remote", label: "À distance", icon: IconRemote },
  { href: "/dashboard/documents", label: "Documents", icon: IconDocument },
];
const PROFILE_LINK = { href: "/dashboard/profile", label: "Profil", icon: IconProfile };
const ADMIN_LINK = { href: "/admin", label: "Admin", icon: IconShield };

export function Navbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <>
      <header className="relative z-10 mx-auto flex w-full max-w-5xl items-center justify-between px-4 pb-4 pt-8">
        <div className="flex items-center gap-2.5">
          <Logo />
          <span className="font-heading text-lg font-bold tracking-tight text-slate-800">AccompFlow</span>
        </div>
        <div className="flex items-center gap-3">
          {user && (
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-accent/15 font-heading text-sm font-bold text-brand-accent">
              {user.name.charAt(0).toUpperCase()}
            </span>
          )}
          <button
            onClick={logout}
            aria-label="Se déconnecter"
            className="flex h-9 w-9 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-sand hover:text-brand"
          >
            <IconLogout width={17} height={17} />
          </button>
        </div>
      </header>
    </>
  );
}

export function NavMenu() {
  const pathname = usePathname();
  const { user } = useAuth();
  const isStaff = user?.role === "owner" || user?.role === "staff";
  const links = isStaff
    ? [HOME_LINK, PROFILE_LINK, ADMIN_LINK]
    : [HOME_LINK, ...CLIENT_LINKS, PROFILE_LINK];

  return (
    <>
      <nav aria-label="Navigation principale" className="relative z-40 flex justify-center px-4 pb-2 pt-8">
        <div className="flex max-w-full items-center gap-1 overflow-x-auto rounded-full bg-white p-1.5 shadow-[0_18px_40px_-14px_rgba(60,40,25,0.35)]">
          {links.map((link) => {
            const active = pathname === link.href;
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  "flex shrink-0 flex-col items-center gap-0.5 rounded-full px-4 py-2 transition-colors",
                  active ? "bg-brand text-white" : "text-slate-500 hover:bg-sand hover:text-brand"
                )}
              >
                <Icon width={19} height={19} />
                <span className="text-[10.5px] font-semibold leading-none">{link.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
