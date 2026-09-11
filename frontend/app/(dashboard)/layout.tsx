import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="relative flex min-h-screen flex-col overflow-x-hidden bg-cream">
        <div aria-hidden className="pointer-events-none absolute -right-24 -top-32 h-80 w-80 rounded-full bg-brand-accent/15 blur-3xl" />
        <div aria-hidden className="pointer-events-none absolute -left-20 top-72 h-64 w-64 rounded-full bg-brand-light/20 blur-3xl" />
        <Navbar />
        <main className="relative mx-auto w-full max-w-5xl flex-1 px-4 pt-2">{children}</main>
        <Footer />
      </div>
    </ProtectedRoute>
  );
}
