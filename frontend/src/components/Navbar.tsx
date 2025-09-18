"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { pingHealth } from "@/lib/api";

export default function Navbar() {
  const [ok, setOk] = useState<"checking"|"ok"|"fail">("checking");
  useEffect(() => { pingHealth().then(setOk).catch(()=>setOk("fail")); }, []);
  const badge = ok==="ok" ? "bg-green-500" : ok==="fail" ? "bg-red-500" : "bg-gray-400";
  return (
    <header className="border-b">
      <div className="mx-auto max-w-5xl px-5 py-3 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold">급식줍쇼</Link>
        <nav className="flex items-center gap-4">
          <Link href="/student" className="px-3 py-1 rounded-lg hover:bg-gray-100">식단 분석·영양</Link>
          <Link href="/nutritionist" className="px-3 py-1 rounded-lg hover:bg-gray-100">영양사·식단표</Link>
          <Link href="/workflow" className="px-3 py-1 rounded-lg hover:bg-gray-100">LLM과 ARP기반 대안 생성</Link>
          <span className={`inline-block w-2 h-2 rounded-full ${badge}`} title="backend health" />
          <Link href="/signup" className="text-sm text-blue-600">회원가입</Link>
        </nav>
      </div>
    </header>
  );
}