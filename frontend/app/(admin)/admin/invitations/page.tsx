"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Invitation } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { Input } from "@/components/ui/Input";

export default function InvitationsPage() {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [lastUrl, setLastUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deletingToken, setDeletingToken] = useState<string | null>(null);

  const loadInvitations = async () => {
    setLoading(true);
    setLoadError(false);
    try {
      const { data } = await api.get<Invitation[]>("/admin/invitations");
      setInvitations(data);
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    queueMicrotask(() => loadInvitations());
  }, []);

  const supprimer = async (invitation: Invitation) => {
    if (!confirm(`Supprimer l'invitation envoyée à ${invitation.email} ?`)) return;
    setDeletingToken(invitation.token);
    setError(null);
    try {
      await api.delete(`/admin/invitations/${invitation.token}`);
      setInvitations((current) => current.filter((i) => i.token !== invitation.token));
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de la suppression de l'invitation.");
    } finally {
      setDeletingToken(null);
    }
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLastUrl(null);
    setSubmitting(true);
    try {
      const { data } = await api.post("/admin/invitations", { email, name });
      setLastUrl(data.invitation_url);
      setEmail("");
      setName("");
      await loadInvitations();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de la création de l'invitation.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Invitations</h1>
        <p className="mt-1 text-sm text-slate-500">
          Envoie un accès portail et crée automatiquement la fiche client correspondante.
        </p>
      </div>

      <Card>
        <form onSubmit={onSubmit} className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label htmlFor="invitation-nom" className="mb-1.5 block text-sm font-semibold text-slate-700">Nom</label>
            <Input id="invitation-nom" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="flex-1">
            <label htmlFor="invitation-email" className="mb-1.5 block text-sm font-semibold text-slate-700">Email</label>
            <Input id="invitation-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Création…" : "Inviter"}
          </Button>
        </form>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        {lastUrl && (
          <p className="mt-3 break-all rounded-2xl bg-sand/50 p-3 text-xs text-slate-600">
            Lien d&apos;invitation (à transmettre manuellement si l&apos;email n&apos;arrive pas) : <br />
            <span className="font-mono">{lastUrl}</span>
          </p>
        )}
      </Card>

      {loadError ? (
        <ErrorState message="Impossible de charger les invitations." onRetry={loadInvitations} />
      ) : (
      <Card className="overflow-hidden p-0">
        {loading ? (
          <p className="p-5 text-sm text-slate-500">Chargement…</p>
        ) : invitations.length === 0 ? (
          <p className="p-5 text-sm text-slate-500">Aucune invitation envoyée.</p>
        ) : (
          <ul className="divide-y divide-black/5">
            {invitations.map((inv) => (
              <li key={inv.token} className="flex items-center justify-between gap-4 p-5 text-sm">
                <div className="min-w-0">
                  <p className="truncate font-semibold text-slate-800">{inv.name}</p>
                  <p className="truncate text-xs text-slate-400">
                    {inv.email} · {formatDate(inv.created_at)}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  <span
                    className={
                      inv.used
                        ? "rounded-full bg-sand/70 px-2.5 py-1 text-xs font-semibold text-slate-500"
                        : "rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800"
                    }
                  >
                    {inv.used ? "Utilisée" : "En attente"}
                  </span>
                  <button
                    type="button"
                    disabled={deletingToken === inv.token}
                    onClick={() => supprimer(inv)}
                    className="text-xs font-semibold text-red-600 hover:underline disabled:opacity-50"
                  >
                    {deletingToken === inv.token ? "Suppression…" : "Supprimer"}
                  </button>
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
