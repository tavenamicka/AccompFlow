import { fireEvent, render, screen } from "@testing-library/react";
import { ErrorState } from "@/components/ui/ErrorState";

describe("ErrorState", () => {
  it("affiche le message d'erreur", () => {
    render(<ErrorState message="Impossible de charger les clients." />);

    expect(screen.getByText("Impossible de charger les clients.")).toBeInTheDocument();
  });

  it("affiche un message par défaut si aucun n'est fourni", () => {
    render(<ErrorState />);

    expect(screen.getByText(/Une erreur est survenue/)).toBeInTheDocument();
  });

  it("n'affiche pas de bouton Réessayer sans callback", () => {
    render(<ErrorState message="Échec." />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("appelle onRetry au clic sur Réessayer", () => {
    const onRetry = jest.fn();
    render(<ErrorState message="Échec." onRetry={onRetry} />);

    fireEvent.click(screen.getByRole("button", { name: "Réessayer" }));

    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
