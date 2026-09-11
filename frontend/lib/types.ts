export type Role = "owner" | "staff" | "client";

export interface User {
  id: number;
  email: string;
  name: string;
  phone: string | null;
  role: Role;
}

export interface Client {
  id: number;
  user_id: number | null;
  nom: string;
  email: string | null;
  telephone: string | null;
  date_debut_contrat: string;
  forfait_n1_h: number;
  forfait_n2_h: number;
  actif: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export type Niveau = "N1" | "N2" | "N3";

export interface InterventionBloc {
  niveau: Niveau;
  duree_minutes: number;
  description: string;
}

export interface Intervention {
  id: number;
  client_id: number;
  user_id: number | null;
  date_intervention: string;
  niveau: Niveau;
  duree_minutes: number;
  description: string;
  groupe_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface NiveauConso {
  forfait_h: number | null;
  consomme_minutes: number;
  pourcentage: number | null;
}

export interface ClientDashboard {
  client_id: number;
  client_nom: string;
  periode_debut: string;
  periode_fin: string;
  n1: NiveauConso;
  n2: NiveauConso;
  n3: NiveauConso;
  alerte: boolean;
}

export interface Alerte {
  client_id: number;
  client_nom: string;
  niveau: "N1" | "N2";
  pourcentage: number;
}

export interface PeriodeResume {
  periode_id: string;
  periode_debut: string;
  periode_fin: string;
  n1: NiveauConso;
  n2: NiveauConso;
  n3: NiveauConso;
  heures_supp_minutes: number;
}

export interface Rapport extends PeriodeResume {
  client_id: number;
  client_nom: string;
  interventions: Intervention[];
}

export type DocumentType = "facture" | "rapport_intervention" | "autre";

export interface Document {
  id: number;
  document_type: DocumentType;
  period_label: string | null;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  uploaded_at: string;
}

export interface Invitation {
  token: string;
  email: string;
  name: string;
  client_id: number | null;
  created_at: string;
  used: boolean;
}

export interface LoginResponse {
  token: string;
  user: User;
}
