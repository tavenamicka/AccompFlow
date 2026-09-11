import { render, screen } from "@testing-library/react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/lib/auth";

jest.mock("@/lib/auth", () => ({
  useAuth: jest.fn(),
}));

const replace = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
}));

const mockedUseAuth = useAuth as jest.Mock;

describe("ProtectedRoute", () => {
  beforeEach(() => {
    replace.mockClear();
  });

  it("affiche un état de chargement et ne redirige pas tant que l'authentification n'est pas résolue", () => {
    mockedUseAuth.mockReturnValue({ isAuthenticated: false, loading: true });

    render(
      <ProtectedRoute>
        <p>Contenu protégé</p>
      </ProtectedRoute>
    );

    expect(screen.getByText("Chargement…")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("redirige vers /auth/login si non authentifié une fois le chargement terminé", () => {
    mockedUseAuth.mockReturnValue({ isAuthenticated: false, loading: false });

    render(
      <ProtectedRoute>
        <p>Contenu protégé</p>
      </ProtectedRoute>
    );

    expect(replace).toHaveBeenCalledWith("/auth/login");
    expect(screen.queryByText("Contenu protégé")).not.toBeInTheDocument();
  });

  it("affiche le contenu quand l'utilisateur est authentifié", () => {
    mockedUseAuth.mockReturnValue({ isAuthenticated: true, loading: false });

    render(
      <ProtectedRoute>
        <p>Contenu protégé</p>
      </ProtectedRoute>
    );

    expect(screen.getByText("Contenu protégé")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });
});
