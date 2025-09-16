"use client";

import { useEffect, useRef, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { optimizeMealplan, type PlanRow } from "@/lib/api";

export default function NutritionistPage() {
  const [days, setDays] = useState(20);
  const [budget, setBudget] = useState(5370);     // 1인 예산(원)
  const [targetKcal, setTargetKcal] = useState(900);
  const [loading, setLoading] = useState(false);

  const [plan, setPlan] = useState<PlanRow[]>([]);
  const [detail, setDetail] = useState<PlanRow | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 진행 중 요청 취소용 컨트롤러
  const abortRef = useRef<AbortController | null>(null);

  const onOptimize = async () => {
    // 기존 요청이 돌고 있으면 취소
    if (abortRef.current) abortRef.current.abort("superseded");
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);

    try {
      const res = await optimizeMealplan(
        {
          use_preset: true, // 서버 .env 경로 사용
          params: { days, budget_won: budget, target_kcal: targetKcal },
        },
        { signal: controller.signal } // ← AbortSignal 전달
      );

      // 취소된 요청이면 무시
      if (controller.signal.aborted) return;

      const rows = (res.plan as PlanRow[]).filter((p) => typeof p.day === "number");
      setPlan(rows);
      setDetail(null);
    } catch (e: any) {
      // 취소는 정상 흐름이므로 조용히 무시
      if (e?.name === "AbortError" || e?.message?.includes("aborted")) return;
      setError(e?.message ?? "식단 생성 중 오류가 발생했습니다.");
      alert(e?.message ?? "식단 생성 중 오류가 발생했습니다.");
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
      setLoading(false);
    }
  };

  // 컴포넌트 언마운트 시 진행 중 요청 취소
  useEffect(() => {
    return () => abortRef.current?.abort("unmount");
  }, []);

  return (
    <AppShell>
      <div className="grid gap-6">
        <section className="rounded-2xl border p-5 grid gap-3">
          <h2 className="text-xl font-semibold">식단표 생성</h2>
          <p className="text-sm text-gray-500">
            CSV 경로는 서버 <code>.env</code> 프리셋을 사용합니다. (프론트에서 경로 입력 없음)
          </p>

          <div className="grid sm:grid-cols-3 gap-3">
            <label className="text-sm">
              일수
              <input
                type="number"
                className="mt-1 w-full border rounded-lg px-3 py-2"
                value={days}
                onChange={(e) => setDays(Number(e.target.value || 20))}
              />
            </label>
            <label className="text-sm">
              1인 예산(원)
              <input
                type="number"
                className="mt-1 w-full border rounded-lg px-3 py-2"
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value || 0))}
              />
            </label>
            <label className="text-sm">
              목표 칼로리(kcal)
              <input
                type="number"
                className="mt-1 w-full border rounded-lg px-3 py-2"
                value={targetKcal}
                onChange={(e) => setTargetKcal(Number(e.target.value || 0))}
              />
            </label>
          </div>

          <div className="flex gap-3 items-center">
            <button
              type="button"                 // ← form 안이라면 submit 방지
              onClick={onOptimize}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-emerald-600 text-white disabled:opacity-50"
            >
              {loading ? "생성 중…" : "식단표 생성"}
            </button>
          </div>

          {error && <p className="text-sm text-red-600">에러: {error}</p>}
        </section>

        {plan.length > 0 && (
          <section className="grid gap-3">
            <h3 className="font-semibold">결과(달력형 카드)</h3>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {plan.map((d) => (
                <button
                  key={String(d.day)}
                  onClick={() => setDetail(d)}
                  className="min-w-[240px] text-left border rounded-xl p-3 hover:shadow transition"
                >
                  <div className="text-sm text-gray-500">DAY {d.day}</div>
                  <div className="font-semibold truncate">{d.rice}</div>
                  <div className="truncate">{d.soup}</div>
                  <div className="truncate">{d.side1}</div>
                  <div className="truncate">{d.side2}</div>
                  <div className="truncate">{d.side3}</div>
                  <div className="truncate text-blue-600">{d.snack}</div>
                  <div className="mt-2 text-xs text-gray-600">
                    kcal {d.day_kcal.toFixed(0)} · C {d.carb_pct_cal.toFixed(0)}% · P{" "}
                    {d.prot_pct_cal.toFixed(0)}% · F {d.fat_pct_cal.toFixed(0)}%
                  </div>
                </button>
              ))}
            </div>
          </section>
        )}

        {detail && (
          <div className="fixed inset-0 bg-black/20 grid place-items-center p-4" onClick={() => setDetail(null)}>
            <div className="bg-white rounded-2xl p-5 w-[560px] max-w-[95vw]" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-center mb-3">
                <h4 className="font-semibold">DAY {detail.day} · 영양정보</h4>
                <button onClick={() => setDetail(null)} className="text-sm">닫기</button>
              </div>
              <ul className="text-sm space-y-1">
                <li>kcal: {detail.day_kcal.toFixed(0)}</li>
                <li>탄수화물 비중: {detail.carb_pct_cal.toFixed(1)}%</li>
                <li>단백질 비중: {detail.prot_pct_cal.toFixed(1)}%</li>
                <li>지방 비중: {detail.fat_pct_cal.toFixed(1)}%</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

