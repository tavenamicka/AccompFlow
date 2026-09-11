"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";

interface AdminUser {
  id: number;
  name: string;
  email: string;
  client_id: number | null;
}

export default function UtilisateursPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
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

  const supprimer = async (user: AdminUser) => {
    if (!confirm(`Supprimer définitivement le compte de ${user.name} (${user.email}) ? Cette action est irréversible.`)) {
      return;
    }
    setDeletingId(user.id);
    setError(null);
    try {
      await api.delete(`/admin/users/${user.id}`);
      setUsers((current) => current.filter((u) => u.id !== user.id));
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de la suppression du compte.");
    } finally {
      setDeletingId(null);
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
                  <p className="truncate font-semibold text-slate-800">{user.name}</p>
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
                  {user.client_id == null && (
                    <Button size="sm" variant="danger" disabled={deletingId === user.id} onClick={() => supprimer(user)}>
                      {deletingId === user.id ? "Suppression…" : "Supprimer"}
                    </Button>
                  )}
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
