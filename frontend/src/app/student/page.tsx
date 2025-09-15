"use client";

import { useState } from "react";
import { analyzeBeforeAfter, toMediaUrl } from "@/lib/api";
import type { IntakeResult } from "@/lib/api";

export default function StudentAnalyzePage() {
  const [before, setBefore] = useState<File | null>(null);
  const [after, setAfter] = useState<File | null>(null);
  const [tray, setTray] = useState<"high" | "middle">("middle");
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<IntakeResult | null>(null);

  // 막대 목표치 
  const TARGETS = { kcal: 900, carbo: 100, protein: 25, fat: 25 };

  const onAnalyze = async () => {
    if (!before || !after) return alert("전/후 이미지를 모두 선택하세요.");
    try {
      setLoading(true);
      const r = await analyzeBeforeAfter(before, after, { tray_type: tray });
      setRes(r);
    } catch (e: any) {
      alert(e?.message || "분석 실패");
    } finally {
      setLoading(false);
    }
  };

  // 퍼센트 막대
  const Bar = ({
    label, value = 0, max, unit = "",
  }: { label: string; value?: number; max: number; unit?: string }) => {
    const v = Number(value) || 0;
    const m = Math.max(1, Number(max) || 1);
    const pct = Math.max(0, Math.min(100, Math.round((v / m) * 100)));
    return (
      <div className="space-y-1">
        <div className="flex justify-between text-sm text-gray-700">
          <span>{label}</span>
          <span>{v.toFixed(1)} / {m} {unit}</span>
        </div>
        <div className="h-2 w-full rounded bg-gray-200">
          <div className="h-2 rounded bg-blue-600" style={{ width: `${pct}%` }} />
        </div>
      </div>
    );
  };


  const get = (k: string, alt?: string) =>
    (res?.totals as any)?.[k] ?? (alt ? (res?.totals as any)?.[alt] : 0) ?? 0;

  // 별점/리뷰(로컬 상태만)
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");

  return (
    <div className="mx-auto max-w-6xl p-6 space-y-6">
      <h1 className="text-2xl font-bold">급식줍쇼 · 학생 분석</h1>

      {/* 업로드 영역 */}
      <section className="rounded-2xl border p-4 space-y-4">
        <div className="grid gap-3 lg:grid-cols-[240px,1fr,1fr]">
          <label className="flex items-center gap-2">
            <span className="w-24 text-sm text-gray-600">식판 종류</span>
            <select
              className="w-full rounded border px-3 py-2"
              value={tray}
              onChange={(e) => setTray(e.target.value as "high" | "middle")}
            >
              <option value="middle">중등 (28×22cm)</option>
              <option value="high">고등 (37×29cm)</option>
            </select>
          </label>

          <label className="flex items-center gap-2">
            <span className="w-20 text-sm text-gray-600">전(食前)</span>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setBefore(e.target.files?.[0] || null)}
              className="w-full rounded border px-3 py-2"
            />
          </label>

          <label className="flex items-center gap-2">
            <span className="w-20 text-sm text-gray-600">후(食後)</span>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setAfter(e.target.files?.[0] || null)}
              className="w-full rounded border px-3 py-2"
            />
          </label>
        </div>

        <button
          onClick={onAnalyze}
          disabled={loading || !before || !after}
          className="w-full rounded-xl bg-blue-600 text-white py-3 font-medium disabled:opacity-60"
        >
          {loading ? "분석 중..." : "분석하기"}
        </button>
      </section>

      {/* 결과 */}
      {res && (
        <>
          {/*  좌: 이미지 2장  ┃   우: 영양 표 */}
          <section className="grid gap-6 lg:grid-cols-3">
            {/* 좌측 두 장 */}
            <div className="lg:col-span-2 grid gap-6 sm:grid-cols-2">
              <figure className="rounded-2xl border p-4 bg-white overflow-hidden">
                <h3 className="font-semibold mb-2">Before</h3>
                <img
                  className="w-full rounded-lg border object-contain"
                  src={toMediaUrl(res.vis_before)}
                  alt="before"
                />
              </figure>

              <figure className="rounded-2xl border p-4 bg-white overflow-hidden">
                <h3 className="font-semibold mb-2">After</h3>
                <img
                  className="w-full rounded-lg border object-contain"
                  src={toMediaUrl(res.vis_after)}
                  alt="after"
                />
              </figure>
            </div>

            {/* 우측 표 */}
            <aside className="rounded-2xl border p-4 bg-white">
              <h3 className="font-semibold mb-3">영양 성분(합계)</h3>
              <dl className="grid grid-cols-2 gap-3">
                {[
                  ["g_intake", "g_intake"],
                  ["vitA", "vitA", "vit_a"],
                  ["thiamin", "thiamin"],
                  ["riboflavin", "riboflavin"],
                  ["niacin", "niacin"],
                  ["vitC", "vitC", "vit_c"],
                  ["vitD", "vitD", "vit_d"],
                  ["calcium", "calcium"],
                  ["iron", "iron"],
                ].map(([key, label, alt]) => {
                  const val = get(key, alt);
                  return (
                    <div key={key} className="rounded-lg border px-3 py-2">
                      <dt className="text-xs text-gray-500">{label}</dt>
                      <dd className="text-sm font-medium">
                        {typeof val === "number" ? val.toFixed(1) : String(val)}
                      </dd>
                    </div>
                  );
                })}
              </dl>
            </aside>
          </section>

          {/* 아래: 막대바 4개 */}
          <section className="rounded-2xl border p-4 space-y-4">
            <h3 className="font-semibold">총 섭취량 요약</h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <Bar label="칼로리(kcal)" value={res.totals?.kcal} max={TARGETS.kcal} />
              <Bar label="탄수화물(g)" value={get("carbo", "carbohydrate")} max={TARGETS.carbo} />
              <Bar label="단백질(g)" value={res.totals?.protein} max={TARGETS.protein} />
              <Bar label="지방(g)" value={res.totals?.fat} max={TARGETS.fat} />
            </div>
          </section>

          {/* 아래: 리뷰 */}
          <section className="rounded-2xl border p-4 space-y-3">
            <h3 className="font-semibold">오늘 급식 평가</h3>
            <div className="flex gap-1 text-2xl">
              {Array.from({ length: 5 }).map((_, i) => (
                <button
                  key={i}
                  onClick={() => setRating(i + 1)}
                  className={i < rating ? "text-yellow-400" : "text-gray-300 hover:text-yellow-400"}
                  aria-label={`별점 ${i + 1}`}
                  type="button"
                >
                  ★
                </button>
              ))}
            </div>
            <textarea
              className="w-full rounded border px-3 py-2 min-h-[100px]"
              placeholder="후기를 남겨주세요"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
            <div className="text-right">
              <button
                type="button"
                className="px-4 py-2 rounded-lg bg-gray-900 text-white"
                onClick={() => alert(`별점: ${rating}점\n리뷰: ${comment || "(비어있음)"}`)}
              >
                저장
              </button>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
