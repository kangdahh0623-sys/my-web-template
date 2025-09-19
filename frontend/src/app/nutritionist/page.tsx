"use client";

import { useEffect, useRef, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { optimizeMealplan, type PlanRow } from "@/lib/api";

// 샘플 음식 이미지 URL (실제로는 서버에서 받아오거나 static 폴더에서 가져와야 함)
const FOOD_IMAGES: Record<string, string> = {
  // 밥류
  "Rice": "/images/foods/rice.jpg",
  "Fried Rice": "/images/foods/fried-rice.jpg",

  // 국류
  "Kimchi Soup": "/images/foods/kimchi-soup.jpg",
  "Beef Soup": "/images/foods/beef-soup.jpg",

  // 반찬류
  "Bulgogi": "/images/foods/bulgogi.jpg",
  "Steamed Egg": "/images/foods/steamed-egg.jpg",
  "Kimchi": "/images/foods/kimchi.jpg",
  "Pork Cutlet": "/images/foods/pork-cutlet.jpg",
  "Vegetable Salad": "/images/foods/vegetable-salad.jpg",

  // 간식류
  "Apple": "/images/foods/apple.jpg",
};

// 기본 이미지 URL (항상 사용 가능한 placeholder)
const DEFAULT_FOOD_IMAGE = "https://via.placeholder.com/200x150/f3f4f6/9ca3af?text=Food";

// 음식 이미지 가져오기 함수 (오류 방지)
const getFoodImage = (foodName: string): string => {
  const imageUrl = FOOD_IMAGES[foodName];
  // 이미지가 정의되어 있으면 해당 이미지, 아니면 기본 이미지
  return imageUrl || DEFAULT_FOOD_IMAGE;
};

export default function NutritionistPage() {
  const [days, setDays] = useState(20);
  const [budget, setBudget] = useState(5370);
  const [targetKcal, setTargetKcal] = useState(900);
  const [loading, setLoading] = useState(false);

  const [plan, setPlan] = useState<PlanRow[]>([]);
  const [detail, setDetail] = useState<PlanRow | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 페이지네이션 상태
  const [currentPage, setCurrentPage] = useState(0);
  const itemsPerPage = 25; // 5x5 레이아웃을 위해

  const abortRef = useRef<AbortController | null>(null);

  const onOptimize = async () => {
    // 입력값 검증
    if (days <= 0 || days > 365) {
      setError("일수는 1-365 사이여야 합니다.");
      return;
    }
    if (budget <= 0) {
      setError("예산은 0보다 커야 합니다.");
      return;
    }
    if (targetKcal <= 0) {
      setError("목표 칼로리는 0보다 커야 합니다.");
      return;
    }

    if (abortRef.current) abortRef.current.abort("superseded");
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    setCurrentPage(0);

    try {
      console.log("최적화 요청:", { days, budget_won: budget, target_kcal: targetKcal });

      const res = await optimizeMealplan(
        {
          use_preset: true,
          params: { days, budget_won: budget, target_kcal: targetKcal },
        },
        { signal: controller.signal }
      );

      if (controller.signal.aborted) return;

      console.log("최적화 응답:", res);
      console.log("res.plan 타입:", typeof res.plan, "길이:", res.plan?.length);

      if (!res.plan || !Array.isArray(res.plan)) {
        throw new Error("서버에서 유효하지 않은 응답을 받았습니다.");
      }

      // 필터링 전 전체 데이터 확인
      console.log("필터링 전 전체 plan:", res.plan);

      const rows = (res.plan as PlanRow[]).filter((p) => {
        console.log("항목 확인:", p, "day 타입:", typeof p.day, "값:", p.day);
        return typeof p.day === "number" && p.day !== "합계"; // 합계 행 제외
      });

      console.log("필터링 후 rows:", rows, "길이:", rows.length);

      if (rows.length === 0) {
        console.warn("필터링 후 데이터가 없습니다. 원본 데이터를 확인하세요.");
        throw new Error("생성된 식단이 없습니다. 설정을 조정해보세요.");
      }

      setPlan(rows);
      setDetail(null);
    } catch (e: any) {
      if (e?.name === "AbortError" || e?.message?.includes("aborted")) return;

      console.error("최적화 오류:", e);

      const errorMessage = e?.message ?? "식단 생성 중 오류가 발생했습니다.";
      setError(errorMessage);

      // 사용자에게 더 구체적인 안내
      if (errorMessage.includes("timeout") || errorMessage.includes("시간")) {
        alert("처리 시간이 초과되었습니다. 일수를 줄이거나 잠시 후 다시 시도해보세요.");
      } else if (errorMessage.includes("파일") || errorMessage.includes("경로")) {
        alert("서버 설정에 문제가 있습니다. 관리자에게 문의하세요.");
      } else {
        alert(errorMessage);
      }
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
      setLoading(false);
    }
  };

  useEffect(() => {
    return () => abortRef.current?.abort("unmount");
  }, []);

  // 페이지네이션 계산
  const totalPages = Math.ceil(plan.length / itemsPerPage);
  const startIndex = currentPage * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentPlan = plan.slice(startIndex, endIndex);

  // 페이지 변경 함수
  const goToPage = (page: number) => {
    setCurrentPage(Math.max(0, Math.min(page, totalPages - 1)));
  };

  return (
    <AppShell>
      <div className="grid gap-6">
        <section className="rounded-2xl border p-5 grid gap-3 bg-gradient-to-br from-emerald-50 to-green-50">
          <h2 className="text-xl font-semibold text-gray-900">식단표 생성</h2>
          <p className="text-sm text-gray-600">
            CSV 경로는 서버 <code className="bg-gray-100 px-2 py-1 rounded">.env</code> 프리셋을 사용합니다.
          </p>

          <div className="grid sm:grid-cols-3 gap-3">
            <label className="text-sm">
              <span className="block font-medium text-gray-700 mb-1">일수</span>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                value={days}
                onChange={(e) => setDays(Number(e.target.value || 20))}
              />
            </label>
            <label className="text-sm">
              <span className="block font-medium text-gray-700 mb-1">1인 예산(원)</span>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value || 0))}
              />
            </label>
            <label className="text-sm">
              <span className="block font-medium text-gray-700 mb-1">목표 칼로리(kcal)</span>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                value={targetKcal}
                onChange={(e) => setTargetKcal(Number(e.target.value || 0))}
              />
            </label>
          </div>

          <div className="flex gap-3 items-center">
            <button
              type="button"
              onClick={onOptimize}
              disabled={loading}
              className="px-6 py-3 rounded-xl bg-emerald-600 text-white font-medium disabled:opacity-50 hover:bg-emerald-700 transition-colors duration-200"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  생성 중…
                </div>
              ) : (
                "식단표 생성"
              )}
            </button>

            {plan.length > 0 && (
              <span className="text-sm text-gray-600">총 {plan.length}일 식단이 생성되었습니다</span>
            )}
          </div>

          {error && <p className="text-sm text-red-600 bg-red-50 p-2 rounded">⚠️ {error}</p>}
        </section>

        {plan.length > 0 && (
          <section className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">생성된 식단표 ({plan.length}일)</h3>

              {/* 페이지네이션 컨트롤 */}
              {totalPages > 1 && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => goToPage(currentPage - 1)}
                    disabled={currentPage === 0}
                    className="px-3 py-1 rounded bg-gray-100 text-gray-600 disabled:opacity-50 hover:bg-gray-200 transition-colors"
                  >
                    ‹ 이전
                  </button>

                  <div className="flex gap-1">
                    {Array.from({ length: totalPages }, (_, i) => (
                      <button
                        key={i}
                        onClick={() => goToPage(i)}
                        className={`px-3 py-1 rounded text-sm transition-colors ${
                          i === currentPage
                            ? "bg-emerald-600 text-white"
                            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                      >
                        {i + 1}
                      </button>
                    ))}
                  </div>

                  <button
                    onClick={() => goToPage(currentPage + 1)}
                    disabled={currentPage === totalPages - 1}
                    className="px-3 py-1 rounded bg-gray-100 text-gray-600 disabled:opacity-50 hover:bg-gray-200 transition-colors"
                  >
                    다음 ›
                  </button>
                </div>
              )}
            </div>

            {/* 현재 페이지 표시 */}
            <div className="text-sm text-gray-500 text-center">
              {startIndex + 1} - {Math.min(endIndex, plan.length)}일 표시 중 (전체 {plan.length}일) | 페이지당 25일씩 5×5 형태로 표시
            </div>

            {/* 식단 카드들 - 5x5 고정 레이아웃 */}
            <div className="grid grid-cols-5 gap-3">
              {/* 빈 슬롯들로 5x5 그리드 채우기 */}
              {Array.from({ length: 25 }, (_, index) => {
                const dayData = currentPlan[index];
                const row = Math.floor(index / 5) + 1;
                const col = (index % 5) + 1;

                if (!dayData) {
                  // 빈 슬롯 - 아무것도 표시하지 않음
                  return (
                    <div key={`empty-${index}`} className="aspect-square"></div>
                  );
                }

                return (
                  <button
                    key={String(dayData.day)}
                    onClick={() => setDetail(dayData)}
                    className="text-left border-2 border-gray-200 rounded-xl p-3 hover:shadow-lg hover:border-emerald-300 transition-all duration-200 transform hover:scale-102 bg-white aspect-square flex flex-col relative"
                  >
                    {/* 위치 정보 표시 */}
                    <div className="absolute top-1 right-1 text-xs text-gray-400 bg-gray-100 px-1 py-0.5 rounded">
                      {row}행{col}열
                    </div>

                    <div className="text-xs font-bold text-emerald-600 mb-2 bg-emerald-50 px-2 py-1 rounded-full text-center">DAY {dayData.day}</div>

                    {/* 메뉴 목록 - 더 컴팩트하게 */}
                    <div className="space-y-1 mb-2 flex-1">
                      <div className="flex items-center gap-1">
                        <span className="text-xs">🍚</span>
                        <span className="text-xs font-medium text-gray-900 truncate">{dayData.rice}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs">🥣</span>
                        <span className="text-xs text-gray-700 truncate">{dayData.soup}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs">🥬</span>
                        <span className="text-xs text-gray-700 truncate">{dayData.side1}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs">🥕</span>
                        <span className="text-xs text-gray-700 truncate">{dayData.side2}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs">🌶️</span>
                        <span className="text-xs text-gray-700 truncate">{dayData.side3}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs">🍎</span>
                        <span className="text-xs text-blue-600 font-medium truncate">{dayData.snack}</span>
                      </div>
                    </div>

                    {/* 영양 정보 - 하단 고정 */}
                    <div className="pt-2 border-t border-gray-100 mt-auto">
                      <div className="text-xs text-gray-600 mb-1 text-center">
                        <span className="font-semibold text-gray-900">{dayData.day_kcal.toFixed(0)}</span> kcal
                      </div>
                      <div className="grid grid-cols-3 gap-1 text-xs text-gray-500">
                        <div className="text-center">C {dayData.carb_pct_cal.toFixed(0)}%</div>
                        <div className="text-center">P {dayData.prot_pct_cal.toFixed(0)}%</div>
                        <div className="text-center">F {dayData.fat_pct_cal.toFixed(0)}%</div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </section>
        )}

        {/* 상세 모달 */}
        {detail && (
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm grid place-items-center p-4 z-50"
            onClick={() => setDetail(null)}
          >
            <div
              className="bg-white rounded-3xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-6">
                <h4 className="text-2xl font-bold text-gray-900">DAY {detail.day} 상세 정보</h4>
                <button
                  onClick={() => setDetail(null)}
                  className="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors flex items-center justify-center group"
                >
                  <svg className="w-5 h-5 text-gray-500 group-hover:text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="grid lg:grid-cols-2 gap-6">
                <div className="grid lg:grid-cols-2 gap-6">
                  {/* 좌측: 급식판 스타일 메뉴 표시 */}
                  <div className="space-y-4">
                    <h5 className="text-lg font-semibold text-gray-900 mb-4">DAY {detail.day} 급식판</h5>

                    {/* 급식판 레이아웃 */}
                    <div className="bg-gradient-to-br from-gray-100 to-gray-200 rounded-3xl p-6 border-4 border-gray-300 shadow-2xl relative">
                      {/* 급식판 배경 패턴 */}
                      <div className="absolute inset-4 rounded-2xl border-2 border-gray-400/30"></div>

                      {/* 메뉴 배치 - 실제 급식판처럼 */}
                      <div className="relative z-10 grid grid-cols-3 gap-3 h-80">
                        {/* 밥 (왼쪽 위) */}
                        <div className="bg-white rounded-2xl p-3 shadow-lg border-2 border-gray-200 flex flex-col">
                          <div className="text-center mb-2">
                            <span className="text-2xl">🍚</span>
                            <p className="text-xs font-medium text-gray-700">밥</p>
                          </div>
                          <div className="flex-1 rounded-xl bg-gradient-to-br from-yellow-50 to-orange-50 flex items-center justify-center relative overflow-hidden">
                            <div className="text-6xl opacity-20 absolute">🍚</div>
                            <img
                              src={getFoodImage(detail.rice)}
                              alt={detail.rice}
                              className="w-full h-full object-cover absolute inset-0 rounded-xl"
                              style={{ display: 'none' }}
                              onLoad={(e) => (e.target as HTMLImageElement).style.display = 'block'}
                              onError={(e) => (e.target as HTMLImageElement).style.display = 'none'}
                            />
                          </div>
                          <p className="text-xs text-center mt-1 text-gray-600 truncate">{detail.rice}</p>
                        </div>

                        {/* 국 (가운데 위) */}
                        <div className="bg-white rounded-2xl p-3 shadow-lg border-2 border-gray-200 flex flex-col">
                          <div className="text-center mb-2">
                            <span className="text-2xl">🥣</span>
                            <p className="text-xs font-medium text-gray-700">국</p>
                          </div>
                          <div className="flex-1 rounded-xl bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center relative overflow-hidden">
                            <div className="text-6xl opacity-20 absolute">🥣</div>
                            <img
                              src={getFoodImage(detail.soup)}
                              alt={detail.soup}
                              className="w-full h-full object-cover absolute inset-0 rounded-xl"
                              style={{ display: 'none' }}
                              onLoad={(e) => (e.target as HTMLImageElement).style.display = 'block'}
                              onError={(e) => (e.target as HTMLImageElement).style.display = 'none'}
                            />
                          </div>
                          <p className="text-xs text-center mt-1 text-gray-600 truncate">{detail.soup}</p>
                        </div>

                        {/* 간식 (오른쪽 위) */}
                        <div className="bg-white rounded-2xl p-3 shadow-lg border-2 border-blue-200 flex flex-col">
                          <div className="text-center mb-2">
                            <span className="text-2xl">🍎</span>
                            <p className="text-xs font-medium text-blue-700">간식</p>
                          </div>
                          <div className="flex-1 rounded-xl bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center relative overflow-hidden">
                            <div className="text-6xl opacity-20 absolute">🍎</div>
                            <img
                              src={getFoodImage(detail.snack)}
                              alt={detail.snack}
                              className="w-full h-full object-cover absolute inset-0 rounded-xl"
                              style={{ display: 'none' }}
                              onLoad={(e) => (e.target as HTMLImageElement).style.display = 'block'}
                              onError={(e) => (e.target as HTMLImageElement).style.display = 'none'}
                            />
                          </div>
                          <p className="text-xs text-center mt-1 text-blue-600 truncate font-medium">{detail.snack}</p>
                        </div>

                        {/* 반찬 1 (왼쪽 아래) */}
                        <div className="bg-white rounded-2xl p-3 shadow-lg border-2 border-gray-200 flex flex-col">
                          <div className="text-center mb-2">
                            <span className="text-2xl">🥬</span>
                            <p className="text-xs font-medium text-gray-700">반찬1</p>
                          </div>
                          <div className="flex-1 rounded-xl bg-gradient-to-br from-green-50 to-emerald-50 flex items-center justify-center relative overflow-hidden">
                            <div className="text-6xl opacity-20 absolute">🥬</div>
                            <img
                              src={getFoodImage(detail.side1)}
                              alt={detail.side1}
                              className="w-full h-full object-cover absolute inset-0 rounded-xl"
                              style={{ display: 'none' }}
                              onLoad={(e) => (e.target as HTMLImageElement).style.display = 'block'}
                              onError={(e) => (e.target as HTMLImageElement).style.display = 'none'}
                            />
                          </div>
                          <p className="text-xs text-center mt-1 text-gray-600 truncate">{detail.side1}</p>
                        </div>

                        {/* 반찬 2 (가운데 아래) */}
                        <div className="bg-white rounded-2xl p-3 shadow-lg border-2 border-gray-200 flex flex-col">
                          <div className="text-center mb-2">
                            <span className="text-2xl">🥕</span>
                            <p className="text-xs font-medium text-gray-700">반찬2</p>
                          </div>
                          <div className="flex-1 rounded-xl bg-gradient-to-br from-orange-50 to-yellow-50 flex items-center justify-center relative overflow-hidden">
                            <div className="text-6xl opacity-20 absolute">🥕</div>
                            <img
                              src={getFoodImage(detail.side2)}
                              alt={detail.side2}
                              className="w-full h-full object-cover absolute inset-0 rounded-xl"
                              style={{ display: 'none' }}
                              onLoad={(e) => (e.target as HTMLImageElement).style.display = 'block'}
                              onError={(e) => (e.target as HTMLImageElement).style.display = 'none'}
                            />
                          </div>
                          <p className="text-xs text-center mt-1 text-gray-600 truncate">{detail.side2}</p>
                        </div>

                        {/* 반찬 3 (오른쪽 아래) */}
                        <div className="bg-white rounded-2xl p-3 shadow-lg border-2 border-gray-200 flex flex-col">
                          <div className="text-center mb-2">
                            <span className="text-2xl">🌶️</span>
                            <p className="text-xs font-medium text-gray-700">반찬3</p>
                          </div>
                          <div className="flex-1 rounded-xl bg-gradient-to-br from-red-50 to-pink-50 flex items-center justify-center relative overflow-hidden">
                            <div className="text-6xl opacity-20 absolute">🌶️</div>
                            <img
                              src={getFoodImage(detail.side3)}
                              alt={detail.side3}
                              className="w-full h-full object-cover absolute inset-0 rounded-xl"
                              style={{ display: 'none' }}
                              onLoad={(e) => (e.target as HTMLImageElement).style.display = 'block'}
                              onError={(e) => (e.target as HTMLImageElement).style.display = 'none'}
                            />
                          </div>
                          <p className="text-xs text-center mt-1 text-gray-600 truncate">{detail.side3}</p>
                        </div>
                      </div>

                      {/* 급식판 라벨 */}
                      <div className="absolute top-2 left-2 bg-emerald-600 text-white px-3 py-1 rounded-full text-sm font-bold shadow-lg">DAY {detail.day}</div>

                      {/* 칼로리 표시 */}
                      <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm px-3 py-1 rounded-full text-sm font-bold text-gray-700 shadow-lg">{detail.day_kcal.toFixed(0)} kcal</div>
                    </div>

                    {/* 급식판 하단 정보 */}
                    <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl p-4 border border-gray-200">
                      <h6 className="font-medium text-gray-900 mb-2">오늘의 한 상</h6>
                      <div className="text-sm text-gray-600 grid grid-cols-2 gap-2">
                        <div>• 🍚 {detail.rice}</div>
                        <div>• 🥣 {detail.soup}</div>
                        <div>• 🥬 {detail.side1}</div>
                        <div>• 🥕 {detail.side2}</div>
                        <div>• 🌶️ {detail.side3}</div>
                        <div>• 🍎 {detail.snack}</div>
                      </div>
                    </div>
                  </div>

                  {/* 우측: 영양 정보 */}
                  <div className="space-y-4">
                    <h5 className="text-lg font-semibold text-gray-900 mb-4">영양 성분 분석</h5>

                    {/* 주요 영양소 */}
                    <div className="bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl p-4 border border-emerald-100">
                      <h6 className="font-medium text-gray-900 mb-3">칼로리 & 매크로</h6>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-white rounded-lg p-3 text-center border border-gray-100">
                          <div className="text-lg font-bold text-blue-600">{detail.carb_pct_cal.toFixed(1)}%</div>
                          <div className="text-xs text-gray-500">탄수화물</div>
                        </div>
                        <div className="bg-white rounded-lg p-3 text-center border border-gray-100">
                          <div className="text-lg font-bold text-orange-600">{detail.prot_pct_cal.toFixed(1)}%</div>
                          <div className="text-xs text-gray-500">단백질</div>
                        </div>
                        <div className="bg-white rounded-lg p-3 text-center border border-gray-100">
                          <div className="text-lg font-bold text-red-600">{detail.fat_pct_cal.toFixed(1)}%</div>
                          <div className="text-xs text-gray-500">지방</div>
                        </div>
                      </div>
                    </div>

                    {/* 영양소 비율 시각화 */}
                    <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-100">
                      <h6 className="font-medium text-gray-900 mb-3">영양소 균형</h6>
                      <div className="space-y-3">
                        {[
                          { label: "탄수화물", value: detail.carb_pct_cal, color: "bg-blue-500", target: 60 },
                          { label: "단백질", value: detail.prot_pct_cal, color: "bg-orange-500", target: 15 },
                          { label: "지방", value: detail.fat_pct_cal, color: "bg-red-500", target: 25 }
                        ].map((nutrient, idx) => (
                          <div key={idx} className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-700">{nutrient.label}</span>
                              <span className="font-medium">{nutrient.value.toFixed(1)}% <span className="text-gray-500 ml-1">(목표: {nutrient.target}%)</span></span>
                            </div>
                            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${nutrient.color} transition-all duration-700`}
                                style={{ width: `${Math.min(100, nutrient.value)}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* 추가 정보 */}
                    <div className="bg-gradient-to-r from-yellow-50 to-amber-50 rounded-xl p-4 border border-yellow-100">
                      <h6 className="font-medium text-gray-900 mb-3">기타 정보</h6>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>• 추정 식비: {((detail.day_cost || 0)).toFixed(0)}원</div>
                        <div>• 영양 균형: {(
                          detail.carb_pct_cal >= 55 && detail.carb_pct_cal <= 65 &&
                          detail.prot_pct_cal >= 7 && detail.prot_pct_cal <= 20 &&
                          detail.fat_pct_cal >= 15 && detail.fat_pct_cal <= 30
                        )
                          ? "✅ 양호" : "⚠️ 조정 필요"
                        }</div>
                        <div>• 칼로리 달성률: {((detail.day_kcal / targetKcal) * 100).toFixed(1)}%</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
                  <button
                    onClick={() => setDetail(null)}
                    className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
                  >
                    닫기
                  </button>
                  <button
                    onClick={() => {
                      // 식단표 인쇄나 저장 기능을 여기에 추가할 수 있습니다
                      alert(`DAY ${detail.day} 식단표를 저장하시겠습니까?`);
                    }}
                    className="px-6 py-3 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 transition-colors"
                  >
                    저장하기
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
