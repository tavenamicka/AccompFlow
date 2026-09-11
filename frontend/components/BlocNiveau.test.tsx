import { render, screen } from "@testing-library/react";
import { BlocNiveau } from "@/components/BlocNiveau";

describe("BlocNiveau", () => {
  it("affiche la consommation et le forfait en heures", () => {
    render(
      <BlocNiveau
        label="N1 — Assistance"
        niveau="N1"
        conso={{ forfait_h: 4, consomme_minutes: 180, pourcentage: 75 }}
      />
    );

    expect(screen.getByText("N1 — Assistance")).toBeInTheDocument();
    expect(screen.getByText("3.0h")).toBeInTheDocument();
    expect(screen.getByText("/ 4h")).toBeInTheDocument();
  });

  it("n'affiche pas de jauge quand le niveau est hors forfait (N3)", () => {
    const { container } = render(
      <BlocNiveau
        label="N3 — Conseil (hors forfait)"
        niveau="N3"
        conso={{ forfait_h: null, consomme_minutes: 90, pourcentage: null }}
      />
    );

    expect(screen.getByText("1.5h")).toBeInTheDocument();
    expect(container.querySelector(".bg-slate-100")).not.toBeInTheDocument();
  });
});
