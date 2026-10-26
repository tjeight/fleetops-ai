import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "FleetOps AI — Agentic Drone Incident Investigation & Safe Response",
  description: "Evidence-backed agentic drone incident investigation and deterministic safety enforcement dashboard.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-slate-100 antialiased flex flex-col">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-surfaceBorder py-6 text-center text-xs text-slate-500 font-mono">
          FleetOps AI • Independent simulated portfolio project • Deterministic flight safety gate active • No physical flight hardware connected.
        </footer>
      </body>
    </html>
  );
}
