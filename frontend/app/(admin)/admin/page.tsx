"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Alerte } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";

export default function AdminOverviewPage() {
  const [alertes, setAlertes] = useState<Alerte[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = () => {
    setLoading(true);
    setError(false);
    api
      .get<Alerte[]>("/alertes")
      .then(({ data }) => setAlertes(data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    queueMicrotask(() => load());
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Vue d&apos;ensemble</h1>
        <p className="mt-1 text-sm text-slate-500">Les clients qui approchent de la limite de leur forfait.</p>
      </div>

      {error ? (
        <ErrorState message="Impossible de charger les alertes." onRetry={load} />
      ) : (
      <Card>
        <h2 className="mb-4 text-lg font-bold text-slate-800">Alertes forfait (≥ 80%)</h2>
        {loading ? (
          <p className="text-sm text-slate-500">Chargement…</p>
        ) : alertes.length === 0 ? (
          <p className="text-sm text-slate-500">Aucun client au-delà de 80% de son forfait ce mois-ci.</p>
        ) : (
          <ul className="divide-y divide-black/5">
            {alertes.map((a) => {
              const isN1 = a.niveau === "N1";
              const bgClass = isN1 ? "bg-brand/10" : "bg-emerald-100";
              const textClass = isN1 ? "text-brand" : "text-emerald-800";
              return (
                <li key={`${a.client_id}-${a.niveau}`} className="flex items-center justify-between gap-4 py-3">
                  <Link
                    href={`/admin/clients/${a.client_id}`}
                    className="text-sm font-semibold text-brand hover:underline"
                  >
                    {a.client_nom}
                  </Link>
                  <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${bgClass} ${textClass}`}>
                    {a.niveau} — {a.pourcentage}%
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
      )}
    </div>
  );
}
