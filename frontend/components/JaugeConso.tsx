import clsx from "clsx";

interface JaugeConsoProps {
  pourcentage: number | null;
}

export function JaugeConso({ pourcentage }: JaugeConsoProps) {
  const pct = pourcentage ?? 0;
  const largeur = Math.min(pct, 100);
  const couleur = pct >= 100 ? "bg-red-500" : pct >= 80 ? "bg-orange-500" : "bg-brand-accent";

  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div className={clsx("h-full rounded-full transition-all", couleur)} style={{ width: `${largeur}%` }} />
    </div>
  );
}
