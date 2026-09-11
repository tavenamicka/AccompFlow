"use client";

import { ChangeEvent, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Document, User } from "@/lib/types";
import { formatDate, formatFileSize } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";

const MAX_FILE_SIZE = 50 * 1024 * 1024;

export default function DocumentsPage() {
  const [clients, setClients] = useState<User[]>([]);
  const [loadingClients, setLoadingClients] = useState(true);
  const [clientsError, setClientsError] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [docsError, setDocsError] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadClients = () => {
    setLoadingClients(true);
    setClientsError(false);
    api
      .get<User[]>("/admin/users")
      .then(({ data }) => setClients(data))
      .catch(() => setClientsError(true))
      .finally(() => setLoadingClients(false));
  };

  useEffect(() => {
    queueMicrotask(() => loadClients());
  }, []);

  const loadDocuments = async (clientId: number) => {
    setLoadingDocs(true);
    setDocsError(false);
    try {
      const { data } = await api.get<Document[]>(`/admin/users/${clientId}/documents`);
      setDocuments(data);
    } catch {
      setDocsError(true);
    } finally {
      setLoadingDocs(false);
    }
  };

  const onSelectClient = (id: number) => {
    setSelectedId(id);
    setError(null);
    loadDocuments(id);
  };

  const onUpload = async (file: File) => {
    if (!selectedId) return;
    setError(null);
    if (file.size > MAX_FILE_SIZE) {
      setError(`« ${file.name} » dépasse la taille maximale de 50 Mo.`);
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.post(`/admin/users/${selectedId}/documents`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await loadDocuments(selectedId);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de l'envoi du fichier.");
    } finally {
      setUploading(false);
    }
  };

  const onFileInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) onUpload(file);
    event.target.value = "";
  };

  const onDelete = async (documentId: number) => {
    if (!selectedId || !confirm("Supprimer ce document ?")) return;
    await api.delete(`/admin/users/${selectedId}/documents/${documentId}`);
    setDocuments((docs) => docs.filter((d) => d.id !== documentId));
  };

  const selectedClient = clients.find((c) => c.id === selectedId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Documents clients</h1>
        <p className="mt-1 text-sm text-slate-500">
          Déposez un rapport d&apos;intervention ou une facture sur le compte d&apos;un client.
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-[240px_1fr]">
        {clientsError ? (
          <ErrorState message="Impossible de charger la liste des clients." onRetry={loadClients} />
        ) : (
        <Card className="overflow-hidden p-0">
          <ul className="divide-y divide-black/5">
            {loadingClients && <li className="p-5 text-sm text-slate-500">Chargement…</li>}
            {!loadingClients && clients.length === 0 && (
              <li className="p-5 text-sm text-slate-500">Aucun client pour le moment.</li>
            )}
            {clients.map((c) => (
              <li key={c.id}>
                <button
                  onClick={() => onSelectClient(c.id)}
                  className={`w-full px-5 py-3 text-left text-sm transition-colors hover:bg-cream ${
                    selectedId === c.id ? "bg-sand/70 font-semibold text-brand" : "text-slate-700"
                  }`}
                >
                  {c.name}
                  <span className="block text-xs text-slate-400">{c.email}</span>
                </button>
              </li>
            ))}
          </ul>
        </Card>
        )}

        <div className="space-y-4">
          {!selectedClient ? (
            <Card>
              <p className="text-sm text-slate-500">Sélectionnez un client à gauche.</p>
            </Card>
          ) : (
            <>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="block w-full cursor-pointer rounded-3xl border-2 border-dashed border-brand/30 bg-white/60 p-8 text-center transition-colors hover:border-brand hover:bg-white"
              >
                <input ref={fileInputRef} type="file" className="hidden" onChange={onFileInputChange} />
                <p className="text-sm font-semibold text-slate-700">
                  {uploading ? "Envoi en cours…" : `Déposer un document pour ${selectedClient.name}`}
                </p>
                <p className="mt-1 text-xs text-slate-400">50 Mo maximum</p>
              </button>

              {error && <p className="text-sm text-red-600">{error}</p>}

              {docsError ? (
                <ErrorState
                  message="Impossible de charger les documents de ce client."
                  onRetry={() => selectedClient && loadDocuments(selectedClient.id)}
                />
              ) : (
              <Card className="overflow-hidden p-0">
                {loadingDocs ? (
                  <p className="p-5 text-sm text-slate-500">Chargement…</p>
                ) : documents.length === 0 ? (
                  <p className="p-5 text-sm text-slate-500">Aucun document pour ce client.</p>
                ) : (
                  <ul className="divide-y divide-black/5">
                    {documents.map((doc) => (
                      <li key={doc.id} className="flex items-center justify-between gap-4 p-5">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-800">{doc.original_filename}</p>
                          <p className="text-xs text-slate-400">
                            {formatFileSize(doc.file_size)} · {formatDate(doc.uploaded_at)}
                          </p>
                        </div>
                        <Button size="sm" variant="danger" onClick={() => onDelete(doc.id)}>
                          Supprimer
                        </Button>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
