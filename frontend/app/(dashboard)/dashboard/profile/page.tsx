"use client";

import { FormEvent, useState } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PasswordInput } from "@/components/ui/PasswordInput";
import { Card } from "@/components/ui/Card";

export default function ProfilePage() {
  const { user, refreshUser, logout } = useAuth();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(user?.name ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);

  const onSaveProfile = async (event: FormEvent) => {
    event.preventDefault();
    setProfileError(null);
    setProfileSuccess(false);
    setSavingProfile(true);
    try {
      await api.put("/users/me", { name, phone, email });
      await refreshUser();
      setProfileSuccess(true);
      setEditing(false);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setProfileError(typeof detail === "string" ? detail : "Échec de la mise à jour du profil (vérifiez l'adresse email).");
    } finally {
      setSavingProfile(false);
    }
  };

  const onChangePassword = async (event: FormEvent) => {
    event.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);

    if (newPassword.length < 8) {
      setPasswordError("Le nouveau mot de passe doit contenir au moins 8 caractères.");
      return;
    }

    setSavingPassword(true);
    try {
      await api.post("/users/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSuccess(true);
      setCurrentPassword("");
      setNewPassword("");
    } catch (err: any) {
      setPasswordError(err?.response?.data?.detail ?? "Échec du changement de mot de passe.");
    } finally {
      setSavingPassword(false);
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-lg space-y-6">
      <h1 className="text-2xl font-semibold">Profil</h1>

      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-medium">Informations</h2>
          {!editing && (
            <button className="text-sm text-brand hover:underline" onClick={() => { setName(user.name); setEmail(user.email); setPhone(user.phone ?? ""); setEditing(true); }}>
              Modifier
            </button>
          )}
        </div>

        {editing ? (
          <form onSubmit={onSaveProfile} className="space-y-4">
            <div>
              <label htmlFor="profile-nom" className="mb-1 block text-sm font-medium text-slate-700">Nom</label>
              <Input id="profile-nom" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
              <label htmlFor="profile-email" className="mb-1 block text-sm font-medium text-slate-700">Email</label>
              <Input id="profile-email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <label htmlFor="profile-telephone" className="mb-1 block text-sm font-medium text-slate-700">Téléphone</label>
              <Input id="profile-telephone" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+33 6 12 34 56 78" />
            </div>
            {profileError && <p className="text-sm text-red-600">{profileError}</p>}
            <div className="flex gap-2">
              <Button type="submit" disabled={savingProfile}>
                {savingProfile ? "Enregistrement…" : "Enregistrer"}
              </Button>
              <Button type="button" variant="secondary" onClick={() => setEditing(false)}>
                Annuler
              </Button>
            </div>
          </form>
        ) : (
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Nom</dt>
              <dd>{user.name}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Email</dt>
              <dd>{user.email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Téléphone</dt>
              <dd>{user.phone || "—"}</dd>
            </div>
            {profileSuccess && <p className="pt-2 text-sm text-emerald-600">Profil mis à jour.</p>}
          </dl>
        )}
      </Card>

      <Card>
        <h2 className="mb-4 font-medium">Changer de mot de passe</h2>
        <form onSubmit={onChangePassword} className="space-y-4">
          <div>
            <label htmlFor="profile-current-password" className="mb-1 block text-sm font-medium text-slate-700">Mot de passe actuel</label>
            <PasswordInput
              id="profile-current-password"
              autoComplete="current-password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="profile-new-password" className="mb-1 block text-sm font-medium text-slate-700">Nouveau mot de passe</label>
            <PasswordInput
              id="profile-new-password"
              autoComplete="new-password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
          </div>
          {passwordError && <p className="text-sm text-red-600">{passwordError}</p>}
          {passwordSuccess && <p className="text-sm text-emerald-600">Mot de passe modifié.</p>}
          <Button type="submit" disabled={savingPassword}>
            {savingPassword ? "Modification…" : "Modifier le mot de passe"}
          </Button>
        </form>
      </Card>

      <Button variant="secondary" onClick={logout}>
        Se déconnecter
      </Button>
    </div>
  );
}
