"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { RowActionsMenu } from "@/components/ui/RowActionsMenu";

interface AdminUser {
  id: number;
  name: string;
  email: string;
  client_id: number | null;
  client_actif: boolean | null;
}

export default function UtilisateursPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setLoadError(false);
    try {
      const { data } = await api.get<AdminUser[]>("/admin/users");
      setUsers(data);
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    queueMicrotask(() => load());
  }, []);

  const archiver = async (user: AdminUser) => {
    if (user.client_id == null) return;
    setPendingId(user.id);
    setError(null);
    try {
      await api.post(`/clients/${user.client_id}/archiver`);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? `Échec de l'archivage de ${user.name}.`);
    } finally {
      setPendingId(null);
    }
  };

  const reactiver = async (user: AdminUser) => {
    if (user.client_id == null) return;
    setPendingId(user.id);
    setError(null);
    try {
      await api.post(`/clients/${user.client_id}/reactiver`);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? `Échec de la réactivation de ${user.name}.`);
    } finally {
      setPendingId(null);
    }
  };

  const supprimer = async (user: AdminUser) => {
    const message =
      user.client_id != null
        ? `Supprimer définitivement la fiche client et le compte portail de ${user.name} (${user.email}) ? Cette action est irréversible.`
        : `Supprimer définitivement le compte de ${user.name} (${user.email}) ? Cette action est irréversible.`;
    if (!confirm(message)) return;
    setPendingId(user.id);
    setError(null);
    try {
      if (user.client_id != null) {
        await api.delete(`/clients/${user.client_id}`);
      } else {
        await api.delete(`/admin/users/${user.id}`);
      }
      setUsers((current) => current.filter((u) => u.id !== user.id));
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de la suppression du compte.");
    } finally {
      setPendingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Utilisateurs</h1>
        <p className="mt-1 text-sm text-slate-500">Comptes ayant accès au portail client.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {loadError ? (
        <ErrorState message="Impossible de charger la liste des utilisateurs." onRetry={load} />
      ) : (
      <Card className="overflow-hidden p-0">
        {loading ? (
          <p className="p-5 text-sm text-slate-500">Chargement…</p>
        ) : users.length === 0 ? (
          <p className="p-5 text-sm text-slate-500">Aucun compte portail.</p>
        ) : (
          <ul className="divide-y divide-black/5">
            {users.map((user) => (
              <li key={user.id} className="flex items-center justify-between gap-4 p-5 text-sm">
                <div className="min-w-0">
                  <p className="truncate font-semibold text-slate-800">
                    {user.name} {user.client_actif === false && <span className="ml-2 text-xs font-normal text-slate-400">(archivé)</span>}
                  </p>
                  <p className="truncate text-xs text-slate-400">{user.email}</p>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  {user.client_id != null ? (
                    <Link
                      href={`/admin/clients/${user.client_id}`}
                      className="text-xs font-semibold text-brand hover:underline"
                    >
                      Voir la fiche client
                    </Link>
                  ) : (
                    <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-800">
                      Sans fiche client
                    </span>
                  )}
                  <RowActionsMenu
                    disabled={pendingId === user.id}
                    actions={[
                      ...(user.client_id != null
                        ? [
                            user.client_actif
                              ? { label: "Archiver", onClick: () => archiver(user) }
                              : { label: "Réactiver", onClick: () => reactiver(user) },
                          ]
                        : []),
                      { label: "Supprimer", variant: "danger" as const, onClick: () => supprimer(user) },
                    ]}
                  />
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
