import type { Metadata } from "next";
import { Quicksand, Nunito_Sans } from "next/font/google";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

const quicksand = Quicksand({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-heading",
});

const nunitoSans = Nunito_Sans({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "AccompFlow",
  description: "AccompFlow — gestion clients, forfaits et documents pour l'activité de coaching numérique.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className={`${quicksand.variable} ${nunitoSans.variable}`}>
      <body className="flex min-h-screen flex-col bg-cream">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
