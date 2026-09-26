"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AIStatusPill } from "@/components/AIStatusPill";
import { cn } from "@/lib/cn";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/fingerprint", label: "Fingerprint" },
  { href: "/blindspots", label: "Blind Spots" },
  { href: "/timeline", label: "Timeline" },
  { href: "/privacy", label: "Privacy" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-20 border-b hairline bg-bg/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-6 px-4">
        <Link
          href="/"
          className="text-sm font-semibold tracking-[0.2em] text-fg hover:text-accent"
        >
          MIRROR
        </Link>
        <nav className="hidden items-center gap-5 md:flex">
          {LINKS.map((l) => {
            const active =
              l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                className={cn(
                  "text-xs tracking-wide transition-colors",
                  active ? "text-fg" : "text-fg-muted hover:text-fg"
                )}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <AIStatusPill />
        </div>
      </div>
    </header>
  );
}