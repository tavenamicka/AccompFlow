"use client";

import { ChangeEvent, DragEvent, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Document, DocumentType } from "@/lib/types";
import { formatDate, formatFileSize, telechargerBlob } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";

const MAX_FILE_SIZE = 50 * 1024 * 1024;

const FILTRES: { value: DocumentType | "toutes"; label: string }[] = [
  { value: "toutes", label: "Tous" },
  { value: "facture", label: "Factures" },
  { value: "rapport_intervention", label: "Rapports d'intervention" },
  { value: "autre", label: "Autres" },
];

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [filtre, setFiltre] = useState<DocumentType | "toutes">("toutes");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = async (documentType: DocumentType | "toutes" = filtre) => {
    setLoading(true);
    setLoadError(false);
    try {
      const { data } = await api.get<Document[]>("/documents", {
        params: documentType === "toutes" ? undefined : { document_type: documentType },
      });
      setDocuments(data);
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    queueMicrotask(() => loadDocuments(filtre));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtre]);

  const uploadFile = async (file: File) => {
    setError(null);
    if (file.size > MAX_FILE_SIZE) {
      setError(`« ${file.name} » dépasse la taille maximale de 50 Mo.`);
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.post("/documents", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await loadDocuments();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Échec de l'envoi du fichier.");
    } finally {
      setUploading(false);
    }
  };

  const onFileInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) uploadFile(file);
    event.target.value = "";
  };

  const onDrop = (event: DragEvent<HTMLButtonElement>) => {
    event.preventDefault();
    setDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file) uploadFile(file);
  };

  const onDelete = async (id: number) => {
    if (!confirm("Supprimer ce document ?")) return;
    await api.delete(`/documents/${id}`);
    setDocuments((docs) => docs.filter((d) => d.id !== id));
  };

  const onDownload = async (doc: Document) => {
    const response = await api.get(`/documents/${doc.id}`, { responseType: "blob" });
    telechargerBlob(response.data, doc.original_filename);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Documents</h1>
        <p className="mt-1 text-slate-500">Factures, rapports d&apos;intervention et autres documents partagés.</p>
      </div>

      <button
        type="button"
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`block w-full cursor-pointer rounded-3xl border-2 border-dashed p-8 text-center transition-colors ${
          dragOver ? "border-brand bg-white" : "border-brand/30 bg-white/60 hover:border-brand hover:bg-white"
        }`}
      >
        <input ref={fileInputRef} type="file" className="hidden" onChange={onFileInputChange} />
        <p className="text-sm font-semibold text-slate-700">
          {uploading ? "Envoi en cours…" : "Glissez un fichier ici, ou cliquez pour en choisir un"}
        </p>
        <p className="mt-1 text-xs text-slate-400">50 Mo maximum</p>
      </button>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex flex-wrap gap-2">
        {FILTRES.map((f) => (
          <button
            key={f.value}
            onClick={() => setFiltre(f.value)}
            className={`rounded-full px-3.5 py-1.5 text-sm font-semibold transition-colors ${
              filtre === f.value ? "bg-brand text-white" : "bg-white text-slate-500 hover:bg-sand hover:text-brand"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loadError ? (
        <ErrorState message="Impossible de charger vos documents." onRetry={() => loadDocuments()} />
      ) : (
      <Card className="overflow-hidden p-0">
        {loading ? (
          <p className="p-6 text-sm text-slate-500">Chargement…</p>
        ) : documents.length === 0 ? (
          <p className="p-6 text-sm text-slate-500">Aucun document pour le moment.</p>
        ) : (
          <ul className="divide-y divide-black/5">
            {documents.map((doc) => (
              <li key={doc.id} className="flex items-center justify-between gap-4 p-5">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-800">{doc.original_filename}</p>
                  <p className="truncate text-xs text-slate-400">
                    {formatFileSize(doc.file_size)} · {formatDate(doc.uploaded_at)}
                    {doc.period_label && ` · période ${doc.period_label}`}
                  </p>
                </div>
                <div className="flex shrink-0 gap-2">
                  <Button size="sm" variant="secondary" onClick={() => onDownload(doc)}>
                    Télécharger
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => onDelete(doc.id)}>
                    Supprimer
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
