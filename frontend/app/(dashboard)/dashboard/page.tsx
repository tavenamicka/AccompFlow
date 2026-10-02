"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { ClientDashboard } from "@/lib/types";
import { formatDateOnly } from "@/lib/utils";
import { BlocNiveau } from "@/components/BlocNiveau";
import { EcheanciersClient } from "@/components/EcheanciersClient";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { IconRemote, IconDocument, IconProfile } from "@/components/icons";

const ITEMS = [
  {
    href: "/dashboard/remote",
    icon: IconRemote,
    title: "Prise en main à distance",
    description: "Chrome Remote Desktop, TeamViewer.",
  },
  {
    href: "/dashboard/documents",
    icon: IconDocument,
    title: "Documents",
    description: "Vos factures et rapports d'intervention.",
  },
  {
    href: "/dashboard/profile",
    icon: IconProfile,
    title: "Profil",
    description: "Vos coordonnées, mot de passe.",
  },
];

export default function DashboardHomePage() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<ClientDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = () => {
    setLoading(true);
    setError(false);
    api
      .get<ClientDashboard>("/me/dashboard")
      .then(({ data }) => setDashboard(data))
      .catch((err: any) => {
        // 404 = pas de fiche client liée à ce compte (staff, ou client pas
        // encore rattaché) : cas normal, pas une panne — on masque juste le bloc.
        if (err?.response?.status !== 404) setError(true);
        setDashboard(null);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    queueMicrotask(() => load());
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Bienvenue{user ? `, ${user.name.split(" ")[0]}` : ""}</h1>
        <p className="mt-1 text-slate-500">Votre espace client AccompFlow.</p>
      </div>

      {error && <ErrorState message="Impossible de charger votre consommation." onRetry={load} />}

      {!loading && dashboard && (
        <div className="space-y-3">
          <p className="text-sm text-slate-500">
            Consommation de la période du {formatDateOnly(dashboard.periode_debut)} au{" "}
            {formatDateOnly(dashboard.periode_fin)}
          </p>
          <div className="grid gap-4 sm:grid-cols-3">
            <BlocNiveau label="N1 — Assistance" niveau="N1" conso={dashboard.n1} />
            <BlocNiveau label="N2 — Optimisation" niveau="N2" conso={dashboard.n2} />
            <BlocNiveau label="N3 — Conseil (hors forfait)" niveau="N3" conso={dashboard.n3} />
          </div>
        </div>
      )}

      <EcheanciersClient />

      <div className="grid gap-5 sm:grid-cols-3">
        {ITEMS.map(({ href, icon: Icon, title, description }) => (
          <Link key={href} href={href}>
            <Card className="h-full transition-shadow hover:shadow-[0_18px_36px_-16px_rgba(60,40,25,0.4)]">
              <span className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-accent/15 text-brand-accent">
                <Icon width={22} height={22} />
              </span>
              <h2 className="font-bold text-slate-800">{title}</h2>
              <p className="mt-1 text-sm text-slate-500">{description}</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
