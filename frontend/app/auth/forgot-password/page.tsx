"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/auth/forgot-password", { email });
      setSent(true);
    } catch (err: any) {
      setError(
        err?.response?.status === 429
          ? "Trop de tentatives, réessayez dans une minute."
          : "Une erreur est survenue, réessayez plus tard.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <h1 className="mb-1 text-xl font-semibold">Mot de passe oublié</h1>
      {sent ? (
        <>
          <p className="mb-4 text-sm text-slate-600">
            Si un compte existe pour cet email, un lien de réinitialisation vient d&apos;être envoyé. Il est valable 1
            heure.
          </p>
          <Link href="/auth/login" className="text-sm text-blue-600 hover:underline">
            Retour à la connexion
          </Link>
        </>
      ) : (
        <>
          <p className="mb-4 text-sm text-slate-500">
            Saisissez votre email : vous recevrez un lien pour choisir un nouveau mot de passe.
          </p>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">
                Email
              </label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? "Envoi…" : "Envoyer le lien"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm">
            <Link href="/auth/login" className="text-slate-500 hover:underline">
              Retour à la connexion
            </Link>
          </p>
        </>
      )}
    </Card>
  );
}
