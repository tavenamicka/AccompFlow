import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export function ErrorState({
  message = "Une erreur est survenue. Réessayez dans un instant.",
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <Card className="border-red-100 bg-red-50/60">
      <p className="text-sm text-red-700">{message}</p>
      {onRetry && (
        <Button size="sm" variant="secondary" className="mt-3" onClick={onRetry}>
          Réessayer
        </Button>
      )}
    </Card>
  );
}
