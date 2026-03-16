"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/", label: "Overview" },
  { href: "/experiences", label: "Experiences" },
  { href: "/skills", label: "Skills" },
  { href: "/graph", label: "Graph" },
];

export default function NavTabs() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-6">
      {tabs.map((tab) => {
        const active =
          tab.href === "/" ? pathname === "/" : pathname.startsWith(tab.href);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`text-sm py-1 border-b-2 transition-colors ${
              active
                ? "text-engram-purple border-engram-purple"
                : "text-gray-500 border-transparent hover:text-gray-300"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
