"use client";
export default function Hero() {
  return (
    <section className="rounded-3xl bg-gradient-to-br from-slate-50 to-indigo-50/60 p-8 md:p-12">
      {/* 배지 */}
      <span className="inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-white/70 px-3 py-1 text-sm text-indigo-600 shadow-sm">
        <span className="h-2 w-2 rounded-full bg-indigo-500" />
        AI 기반 급식 관리 솔루션
      </span>

      {/* 타이틀 */}
      <h1 className="mt-4 text-4xl md:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-600 to-cyan-600 bg-clip-text text-transparent">
        급식줍쇼
      </h1>

      {/* 설명문 */}
      <p className="mt-3 text-base md:text-lg text-slate-600 leading-relaxed">
        <span className="font-semibold text-indigo-600">학생</span>을 위한 스마트 영양 분석과{" "}
        <span className="font-semibold text-cyan-600">영양사</span>를 위한 데이터 기반 식단 최적화를 제공합니다
      </p>
    </section>
  );
}
