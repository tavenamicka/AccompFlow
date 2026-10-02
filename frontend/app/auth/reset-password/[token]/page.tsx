"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { PasswordInput } from "@/components/ui/PasswordInput";
import { Card } from "@/components/ui/Card";

export default function ResetPasswordPage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Les deux mots de passe ne correspondent pas.");
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/auth/reset-password", { token: params.token, password });
      setDone(true);
      setTimeout(() => router.push("/auth/login"), 2000);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Lien invalide ou expiré.");
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <Card>
        <h1 className="mb-1 text-xl font-semibold">Mot de passe mis à jour</h1>
        <p className="mb-4 text-sm text-slate-600">Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.</p>
        <Link href="/auth/login" className="text-sm text-blue-600 hover:underline">
          Se connecter
        </Link>
      </Card>
    );
  }

  return (
    <Card>
      <h1 className="mb-1 text-xl font-semibold">Nouveau mot de passe</h1>
      <p className="mb-4 text-sm text-slate-500">Choisissez un nouveau mot de passe pour votre compte.</p>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">
            Nouveau mot de passe
          </label>
          <PasswordInput
            id="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="confirmPassword" className="mb-1 block text-sm font-medium text-slate-700">
            Confirmer le mot de passe
          </label>
          <PasswordInput
            id="confirmPassword"
            autoComplete="new-password"
            required
            minLength={8}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Enregistrement…" : "Changer le mot de passe"}
        </Button>
      </form>
      <p className="mt-4 text-center text-sm">
        <Link href="/auth/forgot-password" className="text-slate-500 hover:underline">
          Demander un nouveau lien
        </Link>
      </p>
    </Card>
  );
}
