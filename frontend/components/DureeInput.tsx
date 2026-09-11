import { Input } from "@/components/ui/Input";

export function DureeInput({
  minutes,
  onChange,
  className,
}: {
  minutes: number;
  onChange: (minutes: number) => void;
  className?: string;
}) {
  const heures = Math.floor(minutes / 60);
  const reste = minutes % 60;

  return (
    <div className={`flex items-center gap-1.5 ${className ?? ""}`}>
      <div className="w-16 shrink-0">
        <Input
          type="number"
          min={0}
          aria-label="Heures"
          className="px-2 text-center"
          value={heures}
          onFocus={(e) => e.target.select()}
          onChange={(e) => onChange(Math.max(0, Number(e.target.value) || 0) * 60 + reste)}
        />
      </div>
      <span className="text-sm text-slate-500">h</span>
      <div className="w-16 shrink-0">
        <Input
          type="number"
          min={0}
          max={59}
          aria-label="Minutes"
          className="px-2 text-center"
          value={reste}
          onFocus={(e) => e.target.select()}
          onChange={(e) => onChange(heures * 60 + Math.min(59, Math.max(0, Number(e.target.value) || 0)))}
        />
      </div>
      <span className="text-sm text-slate-500">min</span>
    </div>
  );
}
