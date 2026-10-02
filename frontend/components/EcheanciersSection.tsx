"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Client, Echeancier, TypeEcheance } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { EcheancierCard, TYPE_LABELS } from "@/components/EcheancierCard";

/** Section admin de la fiche client : interrupteur de l'option, puis un
 * échéancier par carte. Gère son propre état pour ne pas démonter les champs
 * en cours d'édition quand la fiche recharge. */
export function EcheanciersSection({ client, onClientChanged }: { client: Client; onClientChanged: (c: Client) => void }) {
  const [echeanciers, setEcheanciers] = useState<Echeancier[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState(false);
  const [titre, setTitre] = useState("");
  const [type, setType] = useState<TypeEcheance>("autre");
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get<Echeancier[]>(`/clients/${client.id}/echeanciers`);
      setEcheanciers(data);
    } catch {
      setError("Impossible de charger les échéanciers.");
    }
  }, [client.id]);

  useEffect(() => {
    if (client.echeanciers_actif) queueMicrotask(() => load());
  }, [client.echeanciers_actif, load]);

  const basculer = async () => {
    setToggling(true);
    setError(null);
    try {
      const { data } = await api.patch<Client>(`/clients/${client.id}`, { echeanciers_actif: !client.echeanciers_actif });
      onClientChanged(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de la modification de l'option.");
    } finally {
      setToggling(false);
    }
  };

  const creer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!titre.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await api.post(`/clients/${client.id}/echeanciers`, { titre: titre.trim(), type_echeance: type });
      setTitre("");
      setType("autre");
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de la création de l'échéancier.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-800">Échéanciers de paiement</h2>
            <p className="text-sm text-slate-500">
              {client.echeanciers_actif
                ? "Option activée : le client voit ses échéanciers (lecture seule) sur son portail."
                : "Option désactivée pour ce client."}
            </p>
          </div>
          <Button variant={client.echeanciers_actif ? "secondary" : "primary"} disabled={toggling} onClick={basculer}>
            {toggling ? "…" : client.echeanciers_actif ? "Désactiver" : "Activer"}
          </Button>
        </div>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </Card>

      {client.echeanciers_actif && (
        <>
          {echeanciers.map((e) => (
            <EcheancierCard key={e.id} echeancier={e} editable onChanged={load} />
          ))}

          <Card>
            <form onSubmit={creer} className="grid items-end gap-3 sm:grid-cols-[1fr_180px_auto]">
              <label className="block text-sm font-semibold text-slate-700">
                Nouvel échéancier
                <Input className="mt-1 font-normal" placeholder="Ex. : Pack 10 séances" value={titre} onChange={(e) => setTitre(e.target.value)} />
              </label>
              <label className="block text-sm font-semibold text-slate-700">
                Type
                <Select className="mt-1 font-normal" value={type} onChange={(e) => setType(e.target.value as TypeEcheance)}>
                  {(Object.keys(TYPE_LABELS) as TypeEcheance[]).map((t) => (
                    <option key={t} value={t}>
                      {TYPE_LABELS[t]}
                    </option>
                  ))}
                </Select>
              </label>
              <Button type="submit" disabled={creating || !titre.trim()}>
                {creating ? "Création…" : "Créer"}
              </Button>
            </form>
          </Card>
        </>
      )}
    </div>
  );
}
