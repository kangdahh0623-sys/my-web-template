"use client";

import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { optimizeMealplan, type PlanRow } from "@/lib/api";

export default function NutritionistPage() {
  // ✅ 경로 입력칸 제거: 프리셋(.env) 경로 사용
  const [days, setDays] = useState(20);
  const [budget, setBudget] = useState(5370);     // 1인 예산(원)
  const [targetKcal, setTargetKcal] = useState(900);
  const [loading, setLoading] = useState(false);

  const [plan, setPlan] = useState<PlanRow[]>([]);
  const [detail, setDetail] = useState<PlanRow | null>(null);

  // ✅ 버튼 클릭 핸들러 (프리셋 사용)
  const onOptimize = async () => {
    setLoading(true);
    try {
      const res = await optimizeMealplan({
        use_preset: true, // ✅ 프리셋 사용 지시 (서버 .env 경로 사용)
        params: { days, budget_won: budget, target_kcal: targetKcal },
      });
      const rows = (res.plan as PlanRow[]).filter((p) => typeof p.day === "number");
      setPlan(rows);
      setDetail(null);
    } catch (e: any) {
      alert(e?.message ?? "최적화 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="grid gap-6">
        {/* 입력 카드: 경로 입력칸 제거, 파라미터만 */}
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
              onClick={onOptimize}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-emerald-600 text-white disabled:opacity-50"
            >
              {loading ? "생성 중…" : "식단표 생성"}
            </button>
          </div>
        </section>

        {/* 결과 카드 그리드 */}
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

        {/* 모달 상세 */}
        {detail && (
          <div
            className="fixed inset-0 bg-black/20 grid place-items-center p-4"
            onClick={() => setDetail(null)}
          >
            <div
              className="bg-white rounded-2xl p-5 w-[560px] max-w-[95vw]"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-3">
                <h4 className="font-semibold">DAY {detail.day} · 영양정보</h4>
                <button onClick={() => setDetail(null)} className="text-sm">
                  닫기
                </button>
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
