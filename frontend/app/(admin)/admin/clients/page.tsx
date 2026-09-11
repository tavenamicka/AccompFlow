"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Client } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { Input } from "@/components/ui/Input";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [recherche, setRecherche] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<number | null>(null);

  const loadClients = async () => {
    setLoading(true);
    setError(false);
    try {
      const { data } = await api.get<Client[]>("/clients");
      setClients(data);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    queueMicrotask(() => loadClients());
  }, []);

  const clientsFiltres = useMemo(() => {
    const q = recherche.trim().toLowerCase();
    if (!q) return clients;
    return clients.filter((c) => c.nom.toLowerCase().includes(q) || (c.email ?? "").toLowerCase().includes(q));
  }, [clients, recherche]);

  const archiverClient = async (client: Client) => {
    setActionError(null);
    setPendingId(client.id);
    try {
      await api.post(`/clients/${client.id}/archiver`);
      await loadClients();
    } catch (err: any) {
      setActionError(err?.response?.data?.detail ?? `Échec de l'archivage de ${client.nom}.`);
    } finally {
      setPendingId(null);
    }
  };

  const reactiverClient = async (client: Client) => {
    setActionError(null);
    setPendingId(client.id);
    try {
      await api.post(`/clients/${client.id}/reactiver`);
      await loadClients();
    } catch (err: any) {
      setActionError(err?.response?.data?.detail ?? `Échec de la réactivation de ${client.nom}.`);
    } finally {
      setPendingId(null);
    }
  };

  const supprimerClient = async (client: Client) => {
    if (!confirm(`Supprimer définitivement la fiche et le compte portail de ${client.nom} ? Cette action est irréversible.`)) return;
    setActionError(null);
    setPendingId(client.id);
    try {
      await api.delete(`/clients/${client.id}`);
      await loadClients();
    } catch (err: any) {
      setActionError(err?.response?.data?.detail ?? `Échec de la suppression de ${client.nom}.`);
    } finally {
      setPendingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Clients</h1>
          <p className="mt-1 text-sm text-slate-500">Fiches, forfaits et accès au portail.</p>
        </div>
        <Button onClick={() => setShowForm((v) => !v)}>{showForm ? "Annuler" : "Nouveau client"}</Button>
      </div>

      {showForm && (
        <NouveauClientForm
          onCreated={() => {
            setShowForm(false);
            loadClients();
          }}
        />
      )}

      <Input
        placeholder="Rechercher par nom ou email…"
        value={recherche}
        onChange={(e) => setRecherche(e.target.value)}
      />

      {actionError && <p className="text-sm text-red-600">{actionError}</p>}

      {error ? (
        <ErrorState message="Impossible de charger la liste des clients." onRetry={loadClients} />
      ) : (
      <Card className="overflow-hidden p-0">
        {loading ? (
          <p className="p-4 text-sm text-slate-500">Chargement…</p>
        ) : clientsFiltres.length === 0 ? (
          <p className="p-4 text-sm text-slate-500">Aucun client.</p>
        ) : (
          <ul className="divide-y divide-black/5">
            {clientsFiltres.map((c) => (
              <li key={c.id} className="flex flex-wrap items-center justify-between gap-3 p-4 hover:bg-cream">
                <Link href={`/admin/clients/${c.id}`} className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-slate-800">
                    {c.nom} {!c.actif && <span className="ml-2 text-xs font-normal text-slate-400">(archivé)</span>}
                  </p>
                  <p className="truncate text-xs text-slate-400">{c.email ?? "—"}</p>
                </Link>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="rounded-full bg-sand/70 px-2.5 py-1 text-xs font-semibold text-slate-600">
                    {c.forfait_n1_h}h N1 · {c.forfait_n2_h}h N2
                  </span>
                  {c.actif ? (
                    <Button
                      variant="secondary"
                      disabled={pendingId === c.id}
                      onClick={() => archiverClient(c)}
                    >
                      Archiver
                    </Button>
                  ) : (
                    <Button
                      variant="secondary"
                      disabled={pendingId === c.id}
                      onClick={() => reactiverClient(c)}
                    >
                      Réactiver
                    </Button>
                  )}
                  <Button
                    variant="danger"
                    disabled={pendingId === c.id}
                    onClick={() => supprimerClient(c)}
                  >
                    {pendingId === c.id ? "…" : "Supprimer"}
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
      )}
    </div>
  );
}

function NouveauClientForm({ onCreated }: { onCreated: () => void }) {
  const [nom, setNom] = useState("");
  const [email, setEmail] = useState("");
  const [telephone, setTelephone] = useState("");
  const [dateDebutContrat, setDateDebutContrat] = useState("");
  const [forfaitN1, setForfaitN1] = useState(4);
  const [forfaitN2, setForfaitN2] = useState(3);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/clients", {
        nom,
        email: email || null,
        telephone: telephone || null,
        date_debut_contrat: dateDebutContrat,
        forfait_n1_h: forfaitN1,
        forfait_n2_h: forfaitN2,
      });
      onCreated();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de la création du client.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="client-nom" className="mb-1.5 block text-sm font-semibold text-slate-700">Nom</label>
          <Input id="client-nom" value={nom} onChange={(e) => setNom(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="client-email" className="mb-1.5 block text-sm font-semibold text-slate-700">Email</label>
          <Input id="client-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <label htmlFor="client-telephone" className="mb-1.5 block text-sm font-semibold text-slate-700">Téléphone</label>
          <Input id="client-telephone" value={telephone} onChange={(e) => setTelephone(e.target.value)} />
        </div>
        <div>
          <label htmlFor="client-debut-contrat" className="mb-1.5 block text-sm font-semibold text-slate-700">Début de contrat</label>
          <Input id="client-debut-contrat" type="date" value={dateDebutContrat} onChange={(e) => setDateDebutContrat(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="client-forfait-n1" className="mb-1.5 block text-sm font-semibold text-slate-700">Forfait N1 (h/mois)</label>
          <Input id="client-forfait-n1" type="number" min={0} value={forfaitN1} onChange={(e) => setForfaitN1(Number(e.target.value))} />
        </div>
        <div>
          <label htmlFor="client-forfait-n2" className="mb-1.5 block text-sm font-semibold text-slate-700">Forfait N2 (h/mois)</label>
          <Input id="client-forfait-n2" type="number" min={0} value={forfaitN2} onChange={(e) => setForfaitN2(Number(e.target.value))} />
        </div>
        <div className="sm:col-span-2">
          {error && <p className="mb-2 text-sm text-red-600">{error}</p>}
          <Button type="submit" disabled={submitting}>
            {submitting ? "Création…" : "Créer le client"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
