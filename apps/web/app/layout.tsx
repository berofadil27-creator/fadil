import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import Header from "@/components/Header";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "VEYRA — Discover What's Real.",
  description: "Comprendre si un texte, une photo ou une vidéo pourrait avoir été créé ou modifié par IA.",
};
export const viewport: Viewport = { themeColor: "#101522" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr">
      <body className={inter.className}>
        <Header />
        <main>{children}</main>
        <footer className="footer">
          <div className="container">
            <span>© 2026 VEYRA · Discover What&apos;s Real.</span>
            <span className="muted">Prototype — aucune analyse n&apos;est encore réelle.</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
