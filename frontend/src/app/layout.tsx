import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";
import { DemoBanner } from "@/components/DemoBanner";

export const metadata: Metadata = {
  title: "MIRROR — AI Digital Twin of Decision Behavior",
  description:
    "MIRROR learns patterns in how you make decisions and builds an evolving computational model of your observable behavior.",
};

export const viewport: Viewport = {
  themeColor: "#0B0D10",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <DemoBanner />
        <Nav />
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
        <footer className="mx-auto max-w-6xl px-4 pb-10 pt-16 text-[11px] text-fg-faint">
          MIRROR models observable interaction behavior inside this application.
          It does not read thoughts or infer private mental states.
        </footer>
      </body>
    </html>
  );
}