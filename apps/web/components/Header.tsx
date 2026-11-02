"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import Logo from "./Logo";

const LINKS = [
  { href: "/analyser", label: "Analyser" },
  { href: "/historique", label: "Historique" },
  { href: "/tarifs", label: "Tarifs" },
  { href: "/compte", label: "Compte" },
];

export default function Header() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <header className="header">
      <div className="container header-inner">
        <Link href="/" aria-label="Accueil VEYRA" onClick={() => setOpen(false)}>
          <Logo />
        </Link>
        <button className="burger" aria-label="Menu" aria-expanded={open} onClick={() => setOpen(!open)}>
          <span /><span /><span />
        </button>
        <nav className={open ? "nav open" : "nav"}>
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className={path === l.href ? "active" : ""} onClick={() => setOpen(false)}>
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
