"use client";

import { useState } from "react";
import clsx from "clsx";
import { api } from "@/lib/api";
import type { Echeance, Echeancier, StatutEcheance, TypeEcheance } from "@/lib/types";
import { formatDateOnly } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { RowActionsMenu } from "@/components/ui/RowActionsMenu";

export const TYPE_LABELS: Record<TypeEcheance, string> = {
  pack: "Pack",
  formation: "Formation",
  autre: "Autre",
};

const DELAI_JOURS = 16;

function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function addDays(iso: string, n: number): string {
  const [y, m, d] = iso.split("-").map(Number);
  const date = new Date(y, m - 1, d + n);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function formatMontant(v: number | null): string {
  if (v == null) return "—";
  return v.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
}

const STATUT_STYLES = {
  retard: ["En retard", "bg-red-100 text-red-800"],
  paye: ["Payé", "bg-emerald-100 text-emerald-800"],
  attente: ["En attente", "border border-slate-300 bg-white text-slate-600"],
} as const;

function statutKey(e: Echeance): keyof typeof STATUT_STYLES {
  return e.en_retard ? "retard" : e.statut === "paye" ? "paye" : "attente";
}

function StatutBadge({ echeance }: { echeance: Echeance }) {
  const [label, cls] = STATUT_STYLES[statutKey(echeance)];
  return <span className={clsx("inline-block rounded-full px-2.5 py-1 text-xs font-semibold", cls)}>{label}</span>;
}

// Champs compacts (32 px) volontairement sans le composant Input : ses classes
// de padding/hauteur de base ne se laissent pas surcharger de façon fiable.
const CHAMP =
  "h-8 w-full min-w-0 rounded-xl border border-slate-200 bg-white px-2 text-[13px] focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/25";

function Champ({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block min-w-0">
      <span className="ech-lbl mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</span>
      {children}
    </label>
  );
}

function EnTeteColonnes() {
  return (
    <div className="ech-grid ech-head pb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
      <span>Facturation</span>
      <span>Échéance</span>
      <span>Montant</span>
      <span>N° facture</span>
      <span>Statut</span>
      <span>Payé le</span>
      <span />
    </div>
  );
}

function EcheanceLigne({ echeance, onChanged }: { echeance: Echeance; onChanged: () => void }) {
  const [draft, setDraft] = useState(echeance);
  const [error, setError] = useState<string | null>(null);
  const [noteOuverte, setNoteOuverte] = useState(false);

  const patch = async (changes: Partial<Echeance>) => {
    setError(null);
    try {
      const { data } = await api.patch<Echeance>(`/echeances/${echeance.id}`, changes);
      setDraft(data);
      onChanged();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de l'enregistrement.");
    }
  };

  const supprimer = async () => {
    if (!confirm("Supprimer cette échéance ?")) return;
    try {
      await api.delete(`/echeances/${echeance.id}`);
      onChanged();
    } catch {
      setError("Échec de la suppression.");
    }
  };

  const changerFacturation = (value: string) => {
    const changes: Partial<Echeance> = { date_facturation: value || null };
    if (value) changes.date_echeance = addDays(value, DELAI_JOURS);
    setDraft({ ...draft, ...changes });
    patch(changes);
  };

  const champTexte = (field: "numero_facture" | "note", value: string) => {
    if ((echeance[field] ?? "") === value) return;
    patch({ [field]: value || null });
  };

  const [statutLabel, statutCls] = STATUT_STYLES[statutKey(draft)];
  const afficherNote = noteOuverte || !!draft.note;

  return (
    <div className="border-t border-black/5 py-2">
      <div className="ech-grid">
        <Champ label="Facturation">
          <input type="date" className={CHAMP} value={draft.date_facturation ?? ""} onChange={(e) => changerFacturation(e.target.value)} />
        </Champ>
        <Champ label="Échéance">
          <input
            type="date"
            className={CHAMP}
            value={draft.date_echeance ?? ""}
            onChange={(e) => {
              setDraft({ ...draft, date_echeance: e.target.value || null });
              patch({ date_echeance: e.target.value || null });
            }}
          />
        </Champ>
        <Champ label="Montant (€)">
          <input
            type="number"
            min="0"
            step="0.01"
            className={clsx(CHAMP, "text-right")}
            value={draft.montant ?? ""}
            onChange={(e) => setDraft({ ...draft, montant: e.target.value === "" ? null : Number(e.target.value) })}
            onBlur={() => draft.montant !== echeance.montant && patch({ montant: draft.montant })}
          />
        </Champ>
        <Champ label="N° de facture">
          <input
            className={CHAMP}
            placeholder="F-2026-001"
            value={draft.numero_facture ?? ""}
            onChange={(e) => setDraft({ ...draft, numero_facture: e.target.value })}
            onBlur={(e) => champTexte("numero_facture", e.target.value)}
          />
        </Champ>
        <Champ label="Statut">
          <span className="relative block h-8">
            <span className={clsx("flex h-8 items-center justify-center gap-1 rounded-full px-3 text-xs font-semibold", statutCls)}>
              {statutLabel}
              <span aria-hidden="true">▾</span>
            </span>
            <select
              aria-label="Statut"
              className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
              value={draft.statut}
              onChange={(e) => {
                const statut = e.target.value as StatutEcheance;
                setDraft({ ...draft, statut });
                patch({ statut });
              }}
            >
              <option value="attente">En attente</option>
              <option value="paye">Payé</option>
            </select>
          </span>
        </Champ>
        <Champ label="Payé le">
          {draft.statut === "paye" ? (
            <input
              type="date"
              className={CHAMP}
              value={draft.date_paiement ?? ""}
              onChange={(e) => {
                setDraft({ ...draft, date_paiement: e.target.value || null });
                patch({ date_paiement: e.target.value || null });
              }}
            />
          ) : (
            <span className="flex h-8 items-center px-2 text-sm text-slate-400">—</span>
          )}
        </Champ>
        <div className="ech-actions">
          <RowActionsMenu
            actions={[
              { label: afficherNote ? "Masquer la note" : "Ajouter une note", onClick: () => setNoteOuverte(!afficherNote) },
              { label: "Supprimer", variant: "danger", onClick: supprimer },
            ]}
          />
        </div>
      </div>
      {afficherNote && (
        <input
          aria-label="Note"
          className={clsx(CHAMP, "mt-2")}
          placeholder="Ex. : acompte, séance 3…"
          value={draft.note ?? ""}
          onChange={(e) => setDraft({ ...draft, note: e.target.value })}
          onBlur={(e) => champTexte("note", e.target.value)}
        />
      )}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}

function Totaux({ echeances }: { echeances: Echeance[] }) {
  const total = echeances.reduce((s, e) => s + (e.montant ?? 0), 0);
  const paye = echeances.filter((e) => e.statut === "paye").reduce((s, e) => s + (e.montant ?? 0), 0);
  const retard = echeances.filter((e) => e.en_retard).length;
  return (
    <p className="text-xs text-slate-600">
      Total {formatMontant(total)} · Payé {formatMontant(paye)} · Reste {formatMontant(total - paye)}
      {retard > 0 && <span className="ml-2 font-semibold text-red-700">{retard} en retard</span>}
    </p>
  );
}

export function EcheancierCard({
  echeancier,
  editable,
  onChanged,
}: {
  echeancier: Echeancier;
  editable: boolean;
  onChanged?: () => void;
}) {
  const [titre, setTitre] = useState(echeancier.titre);
  const [notes, setNotes] = useState(echeancier.notes ?? "");
  const [notesOuvertes, setNotesOuvertes] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const afficherNotes = notesOuvertes || !!echeancier.notes;

  const patchEcheancier = async (changes: Record<string, unknown>) => {
    setError(null);
    try {
      await api.patch(`/echeanciers/${echeancier.id}`, changes);
      onChanged?.();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de l'enregistrement.");
    }
  };

  const supprimerEcheancier = async () => {
    if (!confirm(`Supprimer l'échéancier « ${echeancier.titre} » et toutes ses échéances ?`)) return;
    try {
      await api.delete(`/echeanciers/${echeancier.id}`);
      onChanged?.();
    } catch {
      setError("Échec de la suppression.");
    }
  };

  const ajouterEcheance = async () => {
    setAdding(true);
    setError(null);
    try {
      const today = todayISO();
      await api.post(`/echeanciers/${echeancier.id}/echeances`, {
        date_facturation: today,
        date_echeance: addDays(today, DELAI_JOURS),
      });
      onChanged?.();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de l'ajout.");
    } finally {
      setAdding(false);
    }
  };

  return (
    <Card className="space-y-3 overflow-hidden">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        {editable ? (
          <>
            <input
              aria-label="Titre de l'échéancier"
              className="h-9 min-w-[180px] flex-1 rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/25"
              value={titre}
              onChange={(e) => setTitre(e.target.value)}
              onBlur={() => titre.trim() && titre !== echeancier.titre && patchEcheancier({ titre: titre.trim() })}
            />
            <select
              aria-label="Type d'échéancier"
              className="h-9 w-32 rounded-xl border border-slate-200 bg-white px-2 text-sm focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/25"
              value={echeancier.type_echeance}
              onChange={(e) => patchEcheancier({ type_echeance: e.target.value })}
            >
              {(Object.keys(TYPE_LABELS) as TypeEcheance[]).map((t) => (
                <option key={t} value={t}>
                  {TYPE_LABELS[t]}
                </option>
              ))}
            </select>
          </>
        ) : (
          <div className="flex flex-1 flex-wrap items-center gap-2">
            <h3 className="text-lg font-bold text-slate-800">{echeancier.titre}</h3>
            <span className="rounded-full bg-sand px-2.5 py-1 text-xs font-semibold text-slate-700">
              {TYPE_LABELS[echeancier.type_echeance]}
            </span>
          </div>
        )}
        <Totaux echeances={echeancier.echeances} />
        {editable && (
          <RowActionsMenu
            actions={[
              { label: afficherNotes ? "Masquer les notes" : "Ajouter des notes", onClick: () => setNotesOuvertes(!afficherNotes) },
              { label: "Supprimer l'échéancier", variant: "danger", onClick: supprimerEcheancier },
            ]}
          />
        )}
      </div>

      {editable
        ? afficherNotes && (
            <input
              aria-label="Notes de l'échéancier"
              className={CHAMP}
              placeholder="Notes (facultatif)"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              onBlur={() => notes !== (echeancier.notes ?? "") && patchEcheancier({ notes: notes || null })}
            />
          )
        : echeancier.notes && <p className="text-sm text-slate-500">{echeancier.notes}</p>}

      {echeancier.echeances.length === 0 ? (
        <p className="text-sm text-slate-500">Aucune échéance.</p>
      ) : editable ? (
        <div className="ech-wrap">
          <EnTeteColonnes />
          {echeancier.echeances.map((e) => (
            <EcheanceLigne key={e.id} echeance={e} onChanged={() => onChanged?.()} />
          ))}
        </div>
      ) : (
        <div className="-mx-6 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-sand/60 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-2 font-semibold">Échéance</th>
                <th className="px-4 py-2 font-semibold">Montant</th>
                <th className="px-4 py-2 font-semibold">Facture</th>
                <th className="px-4 py-2 font-semibold">Statut</th>
                <th className="px-4 py-2 font-semibold">Payé le</th>
                <th className="px-4 py-2 font-semibold">Note</th>
              </tr>
            </thead>
            <tbody>
              {echeancier.echeances.map((e) => (
                <tr key={e.id} className={clsx("border-t border-black/5", e.en_retard && "bg-red-50")}>
                  <td className="px-4 py-2">{e.date_echeance ? formatDateOnly(e.date_echeance) : "—"}</td>
                  <td className="px-4 py-2 tabular-nums">{formatMontant(e.montant)}</td>
                  <td className="px-4 py-2">{e.numero_facture ?? "—"}</td>
                  <td className="px-4 py-2">
                    <StatutBadge echeance={e} />
                  </td>
                  <td className="px-4 py-2">{e.statut === "paye" && e.date_paiement ? formatDateOnly(e.date_paiement) : "—"}</td>
                  <td className="px-4 py-2 text-slate-500">{e.note ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editable && (
        <div>
          <Button variant="secondary" size="sm" disabled={adding} onClick={ajouterEcheance}>
            {adding ? "Ajout…" : "Ajouter une échéance"}
          </Button>
        </div>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
    </Card>
  );
}
