"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const active = (href: string) =>
    pathname === href || pathname?.startsWith(href + "/");

  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* Top bar */}
      <header className="border-b">
        <div className="mx-auto max-w-6xl px-5 py-3 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold">급식줍쇼</Link>
          <nav className="hidden sm:flex items-center gap-1 bg-gray-100 rounded-xl p-1">
            <Link
              href="/student"
              className={`px-4 py-1.5 rounded-lg text-sm ${
                active("/student") ? "bg-white shadow font-medium" : "text-gray-600 hover:bg-white/70"
              }`}
            >
              학생 · 분석
            </Link>
            <Link
              href="/nutritionist"
              className={`px-4 py-1.5 rounded-lg text-sm ${
                active("/nutritionist") ? "bg-white shadow font-medium" : "text-gray-600 hover:bg-white/70"
              }`}
            >
              영양사 · 식단표
            </Link>
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="mx-auto max-w-6xl px-5 py-6">{children}</main>
    </div>
  );
}
