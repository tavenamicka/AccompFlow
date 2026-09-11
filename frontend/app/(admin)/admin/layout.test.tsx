import { render, screen } from "@testing-library/react";
import { AdminGuard } from "./layout";
import { useAuth } from "@/lib/auth";

jest.mock("@/lib/auth", () => ({
  useAuth: jest.fn(),
}));

const mockedUseAuth = useAuth as jest.Mock;

describe("AdminGuard", () => {
  it("bloque un compte non connecté", () => {
    mockedUseAuth.mockReturnValue({ user: null });

    render(
      <AdminGuard>
        <p>Section admin</p>
      </AdminGuard>
    );

    expect(screen.getByText(/réservée au personnel/i)).toBeInTheDocument();
    expect(screen.queryByText("Section admin")).not.toBeInTheDocument();
  });

  it("bloque un compte de rôle client", () => {
    mockedUseAuth.mockReturnValue({ user: { role: "client" } });

    render(
      <AdminGuard>
        <p>Section admin</p>
      </AdminGuard>
    );

    expect(screen.getByText(/réservée au personnel/i)).toBeInTheDocument();
  });

  it.each(["owner", "staff"])("autorise un compte de rôle %s", (role) => {
    mockedUseAuth.mockReturnValue({ user: { role } });

    render(
      <AdminGuard>
        <p>Section admin</p>
      </AdminGuard>
    );

    expect(screen.getByText("Section admin")).toBeInTheDocument();
  });
});
