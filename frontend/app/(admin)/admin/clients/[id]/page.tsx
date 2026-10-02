"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Client, ClientDashboard, Intervention, PeriodeResume } from "@/lib/types";
import { formatDateOnly, formatHeures, telechargerBlob } from "@/lib/utils";
import { BlocNiveau } from "@/components/BlocNiveau";
import { EcheanciersSection } from "@/components/EcheanciersSection";
import { InterventionsTable } from "@/components/InterventionsTable";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";

export default function FicheClientPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const clientId = Number(params.id);

  const [client, setClient] = useState<Client | null>(null);
  const [dashboard, setDashboard] = useState<ClientDashboard | null>(null);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [periodes, setPeriodes] = useState<PeriodeResume[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<"pdf" | "xlsx" | null>(null);
  const [inviting, setInviting] = useState(false);
  const [invitationUrl, setInvitationUrl] = useState<string | null>(null);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [editingDate, setEditingDate] = useState(false);
  const [dateDebut, setDateDebut] = useState("");
  const [savingDate, setSavingDate] = useState(false);
  const [dateError, setDateError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [{ data: clientData }, { data: dashboardData }, { data: periodesData }] = await Promise.all([
        api.get<Client>(`/clients/${clientId}`),
        api.get<ClientDashboard>(`/clients/${clientId}/dashboard`),
        api.get<PeriodeResume[]>(`/clients/${clientId}/periodes`),
      ]);
      setClient(clientData);
      setDashboard(dashboardData);
      setPeriodes(periodesData);

      const { data: interventionsData } = await api.get<Intervention[]>("/interventions", {
        params: { client_id: clientId, date_debut: dashboardData.periode_debut, date_fin: dashboardData.periode_fin },
      });
      setInterventions(interventionsData);
    } catch (err: any) {
      setLoadError(
        err?.response?.status === 404
          ? "Ce client n'existe pas ou plus."
          : "Impossible de charger la fiche client."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    queueMicrotask(() => load());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientId]);

  const exporter = async (format: "pdf" | "xlsx") => {
    setExporting(format);
    try {
      const response = await api.get(`/rapports/${clientId}/${format}`, {
        params: { periode: "courante" },
        responseType: "blob",
      });
      const disposition = response.headers["content-disposition"] as string | undefined;
      const filename = disposition?.match(/filename="(.+)"/)?.[1] ?? `rapport.${format}`;
      telechargerBlob(response.data, filename);
    } finally {
      setExporting(null);
    }
  };

  const inviterAuPortail = async () => {
    if (!client?.email) return;
    setInviting(true);
    setInviteError(null);
    try {
      const { data } = await api.post("/admin/invitations", {
        email: client.email,
        name: client.nom,
        client_id: client.id,
      });
      setInvitationUrl(data.invitation_url);
    } catch (err: any) {
      setInviteError(err?.response?.data?.detail ?? "Échec de la création de l'invitation.");
    } finally {
      setInviting(false);
    }
  };

  const sauvegarderDateDebut = async () => {
    if (!client || !dateDebut) return;
    setSavingDate(true);
    setDateError(null);
    try {
      await api.patch(`/clients/${client.id}`, { date_debut_contrat: dateDebut });
      setEditingDate(false);
      await load();
    } catch (err: any) {
      setDateError(err?.response?.data?.detail ?? "Échec de la mise à jour de la date.");
    } finally {
      setSavingDate(false);
    }
  };

  const supprimerClient = async () => {
    if (!client || !confirm(`Supprimer définitivement la fiche de ${client.nom} ? Cette action est irréversible.`)) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await api.delete(`/clients/${client.id}`);
      router.push("/admin/clients");
    } catch (err: any) {
      setDeleteError(err?.response?.data?.detail ?? "Échec de la suppression du client.");
      setDeleting(false);
    }
  };

  if (loading) {
    return <p className="text-sm text-slate-500">Chargement…</p>;
  }

  if (loadError || !client || !dashboard) {
    return <ErrorState message={loadError ?? "Impossible de charger la fiche client."} onRetry={load} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">
            {client.nom} {!client.actif && <span className="ml-2 text-sm font-normal text-slate-400">(archivé)</span>}
          </h1>
          <p className="text-sm text-slate-500">
            {client.email ?? "—"} {client.telephone && `· ${client.telephone}`}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" disabled={exporting !== null} onClick={() => exporter("pdf")}>
            {exporting === "pdf" ? "Génération…" : "Export PDF"}
          </Button>
          <Button variant="secondary" disabled={exporting !== null} onClick={() => exporter("xlsx")}>
            {exporting === "xlsx" ? "Génération…" : "Export Excel"}
          </Button>
          <Link href={`/admin/clients/${clientId}/nouvelle-intervention`}>
            <Button>Nouvelle intervention</Button>
          </Link>
          <Button variant="danger" disabled={deleting} onClick={supprimerClient}>
            {deleting ? "Suppression…" : "Supprimer"}
          </Button>
        </div>
      </div>

      {deleteError && <p className="text-sm text-red-600">{deleteError}</p>}

      <Card>
        {client.user_id != null ? (
          <p className="text-sm">
            <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800">
              Compte portail actif
            </span>
          </p>
        ) : !client.email ? (
          <p className="text-sm text-slate-500">Ajoutez un email au client pour pouvoir l&apos;inviter au portail.</p>
        ) : invitationUrl ? (
          <p className="break-all rounded-2xl bg-sand/50 p-3 text-xs text-slate-600">
            Invitation créée — lien à transmettre si l&apos;email n&apos;arrive pas :<br />
            <span className="font-mono">{invitationUrl}</span>
          </p>
        ) : (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-slate-500">Ce client n&apos;a pas encore de compte portail.</p>
            <Button variant="secondary" disabled={inviting} onClick={inviterAuPortail}>
              {inviting ? "Envoi…" : "Inviter au portail"}
            </Button>
          </div>
        )}
        {inviteError && <p className="mt-2 text-sm text-red-600">{inviteError}</p>}
      </Card>

      <EcheanciersSection client={client} onClientChanged={setClient} />

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-slate-500">
        <p>
          Période du {formatDateOnly(dashboard.periode_debut)} au {formatDateOnly(dashboard.periode_fin)}
        </p>
        {editingDate ? (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sauvegarderDateDebut();
            }}
            className="flex flex-wrap items-center gap-2"
          >
            <label htmlFor="date-debut-contrat" className="text-slate-600">Début du contrat</label>
            <input
              id="date-debut-contrat"
              type="date"
              required
              value={dateDebut}
              onChange={(e) => setDateDebut(e.target.value)}
              className="rounded-xl border border-black/10 bg-white px-3 py-1.5 text-slate-800"
            />
            <Button type="submit" disabled={savingDate}>{savingDate ? "…" : "Enregistrer"}</Button>
            <Button type="button" variant="secondary" onClick={() => setEditingDate(false)}>Annuler</Button>
          </form>
        ) : (
          <button
            className="text-brand hover:underline"
            onClick={() => {
              setDateDebut(client.date_debut_contrat);
              setDateError(null);
              setEditingDate(true);
            }}
          >
            Début du contrat : {formatDateOnly(client.date_debut_contrat)} — modifier
          </button>
        )}
        {dateError && <span className="text-red-600">{dateError}</span>}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <BlocNiveau label="N1 — Assistance" niveau="N1" conso={dashboard.n1} />
        <BlocNiveau label="N2 — Optimisation" niveau="N2" conso={dashboard.n2} />
        <BlocNiveau label="N3 — Conseil (hors forfait)" niveau="N3" conso={dashboard.n3} />
      </div>

      <Card className="overflow-hidden p-0">
        <InterventionsTable interventions={interventions} onChanged={load} />
      </Card>

      <div>
        <h2 className="mb-3 text-lg font-bold text-slate-800">Historique</h2>
        <Card className="overflow-hidden p-0">
          {periodes.length === 0 ? (
            <p className="p-6 text-sm text-slate-500">Aucune période antérieure.</p>
          ) : (
            <table className="min-w-full text-sm">
              <thead className="bg-sand/60 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Période</th>
                  <th className="px-5 py-3 font-semibold">N1</th>
                  <th className="px-5 py-3 font-semibold">N2</th>
                  <th className="px-5 py-3 font-semibold">Heures supp.</th>
                </tr>
              </thead>
              <tbody>
                {periodes.map((p) => (
                  <tr key={p.periode_id} className="border-t border-black/5 transition-colors hover:bg-cream/60">
                    <td className="px-5 py-3">
                      <Link
                        href={`/admin/clients/${clientId}/periodes/${p.periode_id}`}
                        className="font-semibold text-brand hover:underline"
                      >
                        {formatDateOnly(p.periode_debut)} — {formatDateOnly(p.periode_fin)}
                      </Link>
                    </td>
                    <td className="px-5 py-3">{p.n1.pourcentage ?? 0}%</td>
                    <td className="px-5 py-3">{p.n2.pourcentage ?? 0}%</td>
                    <td className="px-5 py-3">{formatHeures(p.heures_supp_minutes)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </div>
  );
}
