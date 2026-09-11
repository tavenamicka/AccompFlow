"use client";

import { FormEvent, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { InterventionBloc, Niveau } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { DureeInput } from "@/components/DureeInput";

const NIVEAUX: Niveau[] = ["N1", "N2", "N3"];

function nouveauBloc(): InterventionBloc {
  return { niveau: "N1", duree_minutes: 30, description: "" };
}

export default function NouvelleInterventionPage() {
  const params = useParams<{ id: string }>();
  const clientId = Number(params.id);
  const router = useRouter();

  const [dateIntervention, setDateIntervention] = useState(() => new Date().toISOString().slice(0, 10));
  const [blocs, setBlocs] = useState<InterventionBloc[]>([nouveauBloc()]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const updateBloc = (index: number, patch: Partial<InterventionBloc>) => {
    setBlocs((current) => current.map((b, i) => (i === index ? { ...b, ...patch } : b)));
  };

  const ajouterBloc = () => setBlocs((current) => [...current, nouveauBloc()]);
  const retirerBloc = (index: number) => setBlocs((current) => current.filter((_, i) => i !== index));

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/interventions", {
        client_id: clientId,
        date_intervention: dateIntervention,
        blocs,
      });
      router.push(`/admin/clients/${clientId}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de l'enregistrement de l'intervention.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Nouvelle intervention</h1>
        <p className="mt-1 text-sm text-slate-500">
          Une intervention peut être scindée sur plusieurs niveaux.
        </p>
      </div>

      <Card>
        <form onSubmit={onSubmit} className="space-y-5">
          <div>
            <label htmlFor="intervention-date" className="mb-1.5 block text-sm font-semibold text-slate-700">Date</label>
            <Input
              id="intervention-date"
              type="date"
              value={dateIntervention}
              onChange={(e) => setDateIntervention(e.target.value)}
              required
            />
          </div>

          <div className="space-y-4">
            {blocs.map((bloc, index) => (
              <div key={index} className="rounded-2xl border border-black/5 bg-cream/60 p-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Bloc {index + 1}</p>
                  {blocs.length > 1 && (
                    <button
                      type="button"
                      onClick={() => retirerBloc(index)}
                      className="text-xs font-semibold text-red-600 hover:underline"
                    >
                      Retirer
                    </button>
                  )}
                </div>
                <div className="mt-3 grid gap-3 sm:grid-cols-[110px_180px_1fr]">
                  <Select
                    value={bloc.niveau}
                    onChange={(e) => updateBloc(index, { niveau: e.target.value as Niveau })}
                  >
                    {NIVEAUX.map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </Select>
                  <DureeInput
                    minutes={bloc.duree_minutes}
                    onChange={(duree_minutes) => updateBloc(index, { duree_minutes })}
                  />
                  <Input
                    placeholder="Description"
                    value={bloc.description}
                    onChange={(e) => updateBloc(index, { description: e.target.value })}
                    required
                  />
                </div>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={ajouterBloc}
            className="block text-sm font-semibold text-brand hover:underline"
          >
            + Scinder sur un autre niveau
          </button>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Enregistrement…" : "Enregistrer"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
