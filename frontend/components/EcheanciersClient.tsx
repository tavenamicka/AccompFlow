"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Echeancier } from "@/lib/types";
import { EcheancierCard } from "@/components/EcheancierCard";

/** Vue portail : tous les échéanciers du client, en lecture seule. Rien n'est
 * rendu si l'option n'est pas activée (liste vide) ou en cas d'erreur — le
 * reste du tableau de bord ne doit pas en dépendre. */
export function EcheanciersClient() {
  const [echeanciers, setEcheanciers] = useState<Echeancier[]>([]);

  useEffect(() => {
    api
      .get<Echeancier[]>("/me/echeanciers")
      .then(({ data }) => setEcheanciers(data))
      .catch(() => setEcheanciers([]));
  }, []);

  if (echeanciers.length === 0) return null;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold text-slate-800">Mes échéanciers</h2>
      {echeanciers.map((e) => (
        <EcheancierCard key={e.id} echeancier={e} editable={false} />
      ))}
    </div>
  );
}
