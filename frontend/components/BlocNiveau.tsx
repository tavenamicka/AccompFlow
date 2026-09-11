import type { NiveauConso } from "@/lib/types";
import { formatHeures } from "@/lib/utils";
import { JaugeConso } from "@/components/JaugeConso";

const COULEURS_TEXTE: Record<string, string> = {
  N1: "text-blue-800",
  N2: "text-teal-800",
  N3: "text-purple-800",
};

interface BlocNiveauProps {
  label: string;
  niveau: "N1" | "N2" | "N3";
  conso: NiveauConso;
}

export function BlocNiveau({ label, niveau, conso }: BlocNiveauProps) {
  return (
    <div className="rounded-3xl border border-black/5 bg-white p-4 shadow-[0_14px_30px_-18px_rgba(60,40,25,0.35)]">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`mt-1 text-xl font-bold ${COULEURS_TEXTE[niveau]}`}>
        {formatHeures(conso.consomme_minutes)}
        {conso.forfait_h !== null && (
          <span className="text-sm font-normal text-slate-500"> / {conso.forfait_h}h</span>
        )}
      </p>
      {conso.forfait_h !== null && (
        <div className="mt-2">
          <JaugeConso pourcentage={conso.pourcentage} />
        </div>
      )}
    </div>
  );
}
