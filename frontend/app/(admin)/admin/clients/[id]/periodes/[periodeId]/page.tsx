"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Rapport } from "@/lib/types";
import { formatDateOnly, telechargerBlob } from "@/lib/utils";
import { BlocNiveau } from "@/components/BlocNiveau";
import { InterventionsTable } from "@/components/InterventionsTable";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";

export default function PeriodeDetailPage() {
  const params = useParams<{ id: string; periodeId: string }>();
  const clientId = Number(params.id);
  const periodeId = params.periodeId;

  const [rapport, setRapport] = useState<Rapport | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<"pdf" | "xlsx" | null>(null);

  const load = () => {
    setLoading(true);
    setLoadError(null);
    return api
      .get<Rapport>(`/clients/${clientId}/periodes/${periodeId}`)
      .then(({ data }) => setRapport(data))
      .catch((err: any) => {
        setLoadError(
          err?.response?.status === 404 ? "Cette période est introuvable." : "Impossible de charger cette période."
        );
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    queueMicrotask(() => load());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientId, periodeId]);

  const exporter = async (format: "pdf" | "xlsx") => {
    setExporting(format);
    try {
      const response = await api.get(`/rapports/${clientId}/${format}`, {
        params: { periode: periodeId },
        responseType: "blob",
      });
      const disposition = response.headers["content-disposition"] as string | undefined;
      const filename = disposition?.match(/filename="(.+)"/)?.[1] ?? `rapport.${format}`;
      telechargerBlob(response.data, filename);
    } finally {
      setExporting(null);
    }
  };

  if (loading) {
    return <p className="text-sm text-slate-500">Chargement…</p>;
  }

  if (loadError || !rapport) {
    return <ErrorState message={loadError ?? "Impossible de charger cette période."} onRetry={load} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            href={`/admin/clients/${clientId}`}
            className="text-sm font-semibold text-brand hover:underline"
          >
            &larr; {rapport.client_nom}
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-slate-800">
            Période du {formatDateOnly(rapport.periode_debut)} au {formatDateOnly(rapport.periode_fin)}
          </h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" disabled={exporting !== null} onClick={() => exporter("pdf")}>
            {exporting === "pdf" ? "Génération…" : "Export PDF"}
          </Button>
          <Button variant="secondary" disabled={exporting !== null} onClick={() => exporter("xlsx")}>
            {exporting === "xlsx" ? "Génération…" : "Export Excel"}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <BlocNiveau label="N1 — Assistance" niveau="N1" conso={rapport.n1} />
        <BlocNiveau label="N2 — Optimisation" niveau="N2" conso={rapport.n2} />
        <BlocNiveau label="N3 — Conseil (hors forfait)" niveau="N3" conso={rapport.n3} />
      </div>

      <Card className="overflow-hidden p-0">
        <InterventionsTable interventions={rapport.interventions} onChanged={load} />
      </Card>
    </div>
  );
}
