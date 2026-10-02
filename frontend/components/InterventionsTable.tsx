"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { Intervention, Niveau } from "@/lib/types";
import { formatDateOnly, formatMinutes } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { Select } from "@/components/ui/Select";
import { RowActionsMenu } from "@/components/ui/RowActionsMenu";
import { DureeInput } from "@/components/DureeInput";

const NIVEAU_BADGE: Record<string, string> = {
  N1: "bg-blue-100 text-blue-800",
  N2: "bg-teal-100 text-teal-800",
  N3: "bg-purple-100 text-purple-800",
};

const NIVEAUX: Niveau[] = ["N1", "N2", "N3"];

export function InterventionsTable({
  interventions,
  onChanged,
}: {
  interventions: Intervention[];
  onChanged?: () => void;
}) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<{
    date_intervention: string;
    niveau: Niveau;
    duree_minutes: number;
    description: string;
  } | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  if (interventions.length === 0) {
    return <p className="p-6 text-center text-sm text-slate-500">Aucune intervention sur cette période.</p>;
  }

  const commencerEdition = (i: Intervention) => {
    setEditingId(i.id);
    setError(null);
    setForm({
      date_intervention: i.date_intervention,
      niveau: i.niveau,
      duree_minutes: i.duree_minutes,
      description: i.description,
    });
  };

  const annulerEdition = () => {
    setEditingId(null);
    setForm(null);
    setError(null);
  };

  const enregistrer = async (id: number) => {
    if (!form) return;
    setSaving(true);
    setError(null);
    try {
      await api.patch(`/interventions/${id}`, form);
      setEditingId(null);
      setForm(null);
      onChanged?.();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de la mise à jour de l'intervention.");
    } finally {
      setSaving(false);
    }
  };

  const supprimer = async (i: Intervention) => {
    if (!confirm("Supprimer définitivement cette intervention ? Cette action est irréversible.")) return;
    setDeletingId(i.id);
    setError(null);
    try {
      await api.delete(`/interventions/${i.id}`);
      onChanged?.();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de la suppression de l'intervention.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="overflow-x-auto">
      {error && <p className="px-3.5 pt-4 text-sm text-red-600">{error}</p>}
      <table className="min-w-full text-sm">
        <thead className="bg-sand/60 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-3.5 py-3 font-semibold">Date</th>
            <th className="px-3.5 py-3 font-semibold">Niveau</th>
            <th className="px-3.5 py-3 font-semibold">Durée</th>
            <th className="px-3.5 py-3 font-semibold">Description</th>
            <th className="px-3.5 py-3" />
          </tr>
        </thead>
        <tbody>
          {interventions.map((i) =>
            editingId === i.id && form ? (
              <tr key={i.id} className="border-t border-black/5 bg-cream align-top">
                <td className="px-3.5 py-3">
                  <div className="w-36">
                    <Input
                      type="date"
                      value={form.date_intervention}
                      onChange={(e) => setForm({ ...form, date_intervention: e.target.value })}
                    />
                  </div>
                </td>
                <td className="px-3.5 py-3">
                  <div className="w-20">
                    <Select
                      value={form.niveau}
                      onChange={(e) => setForm({ ...form, niveau: e.target.value as Niveau })}
                    >
                      {NIVEAUX.map((n) => (
                        <option key={n} value={n}>
                          {n}
                        </option>
                      ))}
                    </Select>
                  </div>
                </td>
                <td className="px-3.5 py-3">
                  <DureeInput minutes={form.duree_minutes} onChange={(duree_minutes) => setForm({ ...form, duree_minutes })} />
                </td>
                <td className="w-full min-w-[20rem] px-3.5 py-3">
                  <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                </td>
                <td className="whitespace-nowrap px-3.5 py-3">
                  <div className="flex gap-2">
                    <Button size="sm" disabled={saving} onClick={() => enregistrer(i.id)}>
                      {saving ? "…" : "Enregistrer"}
                    </Button>
                    <Button size="sm" variant="secondary" disabled={saving} onClick={annulerEdition}>
                      Annuler
                    </Button>
                  </div>
                </td>
              </tr>
            ) : (
              <tr key={i.id} className="border-t border-black/5 transition-colors hover:bg-cream/60">
                <td className="px-3.5 py-3">{formatDateOnly(i.date_intervention)}</td>
                <td className="px-3.5 py-3">
                  <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${NIVEAU_BADGE[i.niveau]}`}>
                    {i.niveau}
                  </span>
                </td>
                <td className="px-3.5 py-3">{formatMinutes(i.duree_minutes)}</td>
                <td className="max-w-md whitespace-pre-wrap break-words px-3.5 py-3">{i.description}</td>
                <td className="whitespace-nowrap px-3.5 py-3">
                  <RowActionsMenu
                    disabled={deletingId === i.id}
                    actions={[
                      { label: "Modifier", onClick: () => commencerEdition(i) },
                      { label: "Supprimer", variant: "danger", onClick: () => supprimer(i) },
                    ]}
                  />
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>
    </div>
  );
}
