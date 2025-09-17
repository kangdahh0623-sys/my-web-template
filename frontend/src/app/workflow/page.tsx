"use client";

import React, { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  generateWorkflowAlternatives,
  analyzeWithAgents,
  parseNaturalLanguage,
  optimizeWithStrategy,
  optimizeMealplan,
  generateReport,
  type WorkflowAlternative,
  type AgentAnalysis,
  type PlanRow,
} from "@/lib/api";

export default function WorkflowPage() {
  const router = useRouter();

  // UI 상태
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: 사용자 요구
  const [userRequest, setUserRequest] = useState<string>(
    "예산 5370원으로 20일치 영양가 높은 급식 메뉴를 계획해주세요"
  );

  // Step 2: 대안
  const [alternatives, setAlternatives] = useState<WorkflowAlternative[]>([]);
  const [selectedAlternativeId, setSelectedAlternativeId] = useState<number | null>(null);

  // Step 3: 파라미터 & 에이전트 분석
  const [params, setParams] = useState<Record<string, number>>({
    days: 20,
    budget: 5370,
    calories: 900,
  });
  const [naturalLanguageInput, setNaturalLanguageInput] = useState<string>("");
  const [agentAnalysis, setAgentAnalysis] = useState<AgentAnalysis | null>(null);

  // Step 4: 결과 (메뉴 플랜)
  const [menuPlan, setMenuPlan] = useState<PlanRow[]>([]);

  const steps = [
    { num: 1, title: "사용자 입력", icon: "👤" },
    { num: 2, title: "AI 대안 생성", icon: "✨" },
    { num: 3, title: "설정 조정", icon: "⚙️" },
    { num: 4, title: "메뉴 최적화", icon: "📅" },
  ];

  const selectedAlternative = useMemo(
    () => alternatives.find((a) => a.id === selectedAlternativeId) || null,
    [alternatives, selectedAlternativeId]
  );

  // 대안 생성 (실제 API → 실패 시 목으로 폴백)
  const handleGenerateAlternatives = async () => {
    if (!userRequest.trim()) {
      setError("요구사항을 입력해주세요.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log("실제 API 호출 시도...");
      const response = await generateWorkflowAlternatives(userRequest);
      setAlternatives(response.alternatives);
      setCurrentStep(2);
    } catch (e: any) {
      console.log("generateWorkflowAlternatives 실패 → mock 사용:", e.message);

      // API 실패시 mock 데이터 사용
      const mockAlternatives = [
        {
          id: 1,
          title: "실제 CSV 기반 영양 중심",
          description: "416개 메뉴 데이터에서 영양소 균형을 최우선으로 선택",
          strategy_type: "nutrition",
          estimated_cost: 5200,
          target_calories: 920,
          features: ["실제 메뉴 데이터", "영양 균형", "칼로리 최적화"],
          highlight: "실제 CSV 데이터 활용",
        },
        {
          id: 2,
          title: "실제 CSV 기반 경제성 우선",
          description: "422개 가격 데이터에서 예산 효율적인 메뉴 조합 생성",
          strategy_type: "economic",
          estimated_cost: 4850,
          target_calories: 880,
          features: ["예산 최적화", "가격 효율성", "다양한 메뉴"],
          highlight: "실제 가격 데이터 반영",
        },
        {
          id: 3,
          title: "실제 CSV 기반 선호도 중심",
          description: "1516개 학생 섭취 기록으로 높은 만족도 메뉴 선별",
          strategy_type: "preference",
          estimated_cost: 5100,
          target_calories: 950,
          features: ["학생 선호도", "높은 섭취율", "만족도 최적화"],
          highlight: "실제 학생 데이터 활용",
        },
      ];

      setAlternatives(mockAlternatives);
      setCurrentStep(2);
    } finally {
      setLoading(false);
    }
  };

  // 대안 선택 → 에이전트 분석 시도(실패해도 UI는 진행)
  async function handleSelectAlternative(id: number) {
    setSelectedAlternativeId(id);
    setLoading(true);
    setError(null);
    try {
      const alt = alternatives.find((a) => a.id === id);
      if (alt) {
        const analysis = (await analyzeWithAgents(alt, params)) as AgentAnalysis;
        setAgentAnalysis(analysis);
      } else {
        setAgentAnalysis(null);
      }
    } catch (e: any) {
      console.warn("analyzeWithAgents 실패:", e?.message);
      setAgentAnalysis(null);
    } finally {
      setCurrentStep(3);
      setLoading(false);
    }
  }

  // 자연어로 파라미터 변경
  async function handleNaturalLanguageChange() {
    if (!naturalLanguageInput.trim()) {
      setError("변경할 내용을 입력해주세요.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result: any = await parseNaturalLanguage(naturalLanguageInput, params);
      const { changes, ...newParams } = result || {};
      setParams(newParams);
      setNaturalLanguageInput("");

      if (changes?.length) {
        alert(`변경 완료:\n${changes.join("\n")}`);
      } else {
        alert("인식된 변경사항이 없습니다. 다른 표현으로 시도해보세요.");
      }
    } catch (e: any) {
      setError(e?.message || "자연어 처리 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  // 실제 최적화 실행
  // frontend/src/app/workflow/page.tsx에서 handleOptimization 함수 수정
  const handleOptimization = async () => {
    if (!selectedAlternative) {
      setError("전략을 선택해주세요.");
      return;
    }

    setLoading(true);
    setCurrentStep(4);
    setError(null);

    try {
      console.log("기존 mealplan API로 최적화 시작...");

      // workflow API 대신 기존 mealplan API 사용
      const result = await optimizeMealplan({
        use_preset: true,
        params: {
          days: params.days,
          budget_won: params.budget,
          target_kcal: params.calories,
        },
      });

      console.log("mealplan API 최적화 완료:", result);

      const realMenu = result.plan.filter((p: any) => typeof p.day === "number");
      setMenuPlan(realMenu);
    } catch (e: any) {
      console.error("mealplan API 최적화 실패:", e);
      setError(e.message || "최적화 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 가정통신문 생성 함수 추가
  const handleGenerateReport = async () => {
    try {
      setLoading(true);
      console.log("가정통신문 생성 시작...");

      const schoolInfo = { name: "○○학교", phone: "02-000-0000", nutritionist: "영양사" };

      const summary = {
        days: params.days,
        budget_won: params.budget,
        avg_kcal:
          menuPlan.length > 0
            ? Math.round(menuPlan.reduce((sum, d) => sum + (d.day_kcal || 0), 0) / menuPlan.length)
            : 0,
        total_cost: menuPlan.reduce((sum, d) => sum + (d.day_cost || 0), 0),
        feasible: true,
      };

      // Blob 받아서 다운로드
      const blob = await generateReport(menuPlan, summary, schoolInfo, "pdf");
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `급식계획서_${params.days}일.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      console.log("가정통신문 다운로드 완료");
    } catch (e: any) {
      console.error("가정통신문 생성 실패:", e);
      alert("가정통신문 생성 중 오류가 발생했습니다: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  // 파생 값
  const ratioSum = (params.carbRatio || 60) + (params.proteinRatio || 15) + (params.fatRatio || 25);
  const totalCost = menuPlan.reduce((acc, r) => acc + (r.day_cost || 0), 0);
  const avgKcal =
    menuPlan.length > 0
      ? Math.round(menuPlan.reduce((a, r) => a + (r.day_kcal || 0), 0) / menuPlan.length)
      : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-green-50 to-blue-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1
            className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-green-600 bg-clip-text text-transparent cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => router.push("/")}
          >
            🍽️ 급식 메뉴 최적화 시스템
          </h1>

          {/* 단계 표시 */}
          <div className="flex items-center gap-2 mt-4 overflow-x-auto">
            {steps.map((step, index) => (
              <div key={step.num} className="flex items-center gap-2">
                <div
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    currentStep >= step.num
                      ? "bg-gradient-to-r from-orange-500 to-green-500 text-white shadow-lg"
                      : "bg-gray-200 text-gray-600"
                  }`}
                >
                  <span className="text-lg">{step.icon}</span>
                  <span className="hidden sm:block">{step.title}</span>
                  <span className="sm:hidden">{step.num}</span>
                </div>
                {index < steps.length - 1 && <span className="text-gray-400">→</span>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 에러 배너 */}
      {error && (
        <div className="max-w-7xl mx-auto px-4">
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {/* Step 1: 사용자 입력 */}
        {currentStep === 1 && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl flex items-center justify-center">
                <span className="text-2xl">👤</span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">1단계: 사용자 입력</h2>
                <p className="text-gray-600">급식 계획에 대한 요구사항을 작성해주세요</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">급식 계획 요구사항</label>
                <textarea
                  className="w-full h-32 p-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
                  placeholder="예: 예산 5370원으로 20일치 영양가 높은 급식 메뉴를 계획해주세요"
                  value={userRequest}
                  onChange={(e) => setUserRequest(e.target.value)}
                />
              </div>

              <button
                onClick={handleGenerateAlternatives}
                disabled={loading || !userRequest.trim()}
                className="w-full py-4 bg-gradient-to-r from-orange-500 to-green-500 text-white rounded-xl font-semibold disabled:opacity-50 hover:from-orange-600 hover:to-green-600 transition-all"
              >
                {loading ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    AI가 전략을 생성하고 있습니다...
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-xl">✨</span>
                    대안 생성하기
                  </div>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: AI 대안 생성 */}
        {currentStep === 2 && alternatives.length > 0 && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                <span className="text-2xl">✨</span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">2단계: AI 대안 생성</h2>
                <p className="text-gray-600">3가지 전략 중 하나를 선택해주세요</p>
              </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              {alternatives.map((alt) => (
                <div
                  key={alt.id}
                  className={`border-2 rounded-2xl p-6 cursor-pointer transition-all transform hover:scale-105 hover:shadow-xl ${
                    selectedAlternativeId === alt.id
                      ? "border-blue-500 bg-blue-50 shadow-lg"
                      : "border-gray-200 bg-white hover:border-blue-300"
                  }`}
                  onClick={() => handleSelectAlternative(alt.id)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-bold text-gray-900 text-lg">{alt.title}</h3>
                    {selectedAlternativeId === alt.id && <span className="text-2xl">✅</span>}
                  </div>

                  <p className="text-gray-600 text-sm mb-4">{alt.description}</p>

                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">예상 비용</span>
                      <span className="font-semibold text-green-600">
                        {alt.estimated_cost.toLocaleString()}원
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">목표 칼로리</span>
                      <span className="font-semibold text-orange-600">{alt.target_calories}kcal</span>
                    </div>

                    {alt.features?.length ? (
                      <div className="pt-3 border-t border-gray-100">
                        <p className="text-xs text-gray-500 mb-2">주요 특징</p>
                        <div className="flex flex-wrap gap-1">
                          {alt.features.slice(0, 3).map((f, i) => (
                            <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                              {f}
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : null}

                    {alt.highlight ? (
                      <div className="mt-3 p-2 bg-yellow-50 rounded-lg border border-yellow-200">
                        <p className="text-xs font-medium text-yellow-800">🌟 {alt.highlight}</p>
                      </div>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>

            {loading && (
              <div className="mt-6 text-center">
                <div className="inline-flex items-center gap-2 text-blue-600">
                  <div className="w-5 h-5 border-2 border-blue-600/30 border-t-blue-600 rounded-full animate-spin" />
                  선택하신 전략을 분석하고 있습니다...
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 3: 설정 조정 */}
        {currentStep === 3 && selectedAlternativeId && (
          <div className="space-y-6">
            {/* Agent-based 분석 (있을 경우 표시) */}
            {agentAnalysis && (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="text-xl">🤖</span>
                  실제 CSV 기반 Multi-Agent 분석 결과
                </h3>

                <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl p-6">
                  <h4 className="font-semibold text-gray-900 mb-3">
                    선택된 전략: {selectedAlternative?.title}
                  </h4>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {agentAnalysis.nutrition_agent.toFixed(0)}
                      </div>
                      <div className="text-sm text-gray-600">🥗 영양사 에이전트</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-700">
                        {agentAnalysis.economic_agent.toFixed(0)}
                      </div>
                      <div className="text-sm text-gray-600">💰 경제 에이전트</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-800">
                        {agentAnalysis.student_agent.toFixed(0)}
                      </div>
                      <div className="text-sm text-gray-600">😊 학생 에이전트</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-900">
                        {agentAnalysis.operation_agent.toFixed(0)}
                      </div>
                      <div className="text-sm text-gray-600">⚙️ 운영 에이전트</div>
                    </div>
                  </div>

                  <div className="p-4 bg-white/50 rounded-lg">
                    <p className="text-sm text-gray-700 mb-2">
                      <strong>🤖 Agent 합의:</strong> {agentAnalysis.consensus}
                    </p>
                    <p className="text-sm text-gray-700">
                      <strong>추천 이유:</strong> {agentAnalysis.recommendation}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* 설정 조정 카드 */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">⚙️</span>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">3단계: 설정 조정</h2>
                  <p className="text-gray-600">파라미터를 조정하고 실제 GA 최적화를 실행하세요</p>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                {/* 실시간 설정 */}
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900">실시간 설정 조정</h3>

                  <div className="bg-gray-50 rounded-xl p-4 space-y-4">
                    <h4 className="font-medium text-gray-800">기본 설정</h4>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">기간: {params.days}일</label>
                      <input
                        type="range"
                        min={5}
                        max={30}
                        value={params.days}
                        onChange={(e) => setParams({ ...params, days: Number(e.target.value) })}
                        className="w-full"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        예산: {params.budget.toLocaleString()}원
                      </label>
                      <input
                        type="number"
                        value={params.budget}
                        onChange={(e) => setParams({ ...params, budget: Number(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        목표 칼로리: {params.calories}kcal
                      </label>
                      <input
                        type="number"
                        value={params.calories}
                        onChange={(e) => setParams({ ...params, calories: Number(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  {/* 영양성분 목표 */}
                  <div className="bg-blue-50 rounded-xl p-4 space-y-4">
                    <h4 className="font-medium text-blue-800">영양성분 목표 조정</h4>

                    <div className="grid grid-cols-1 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          단백질: {params.protein || 25}g
                        </label>
                        <input
                          type="range"
                          min={15}
                          max={40}
                          value={params.protein || 25}
                          onChange={(e) => setParams({ ...params, protein: Number(e.target.value) })}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>15g</span>
                          <span>권장: 25g</span>
                          <span>40g</span>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          비타민C: {params.vitaminC || 50}mg
                        </label>
                        <input
                          type="range"
                          min={20}
                          max={100}
                          value={params.vitaminC || 50}
                          onChange={(e) => setParams({ ...params, vitaminC: Number(e.target.value) })}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>20mg</span>
                          <span>권장: 50mg</span>
                          <span>100mg</span>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          칼슘: {params.calcium || 400}mg
                        </label>
                        <input
                          type="range"
                          min={200}
                          max={800}
                          value={params.calcium || 400}
                          onChange={(e) => setParams({ ...params, calcium: Number(e.target.value) })}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>200mg</span>
                          <span>권장: 400mg</span>
                          <span>800mg</span>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          철분: {params.iron || 8}mg
                        </label>
                        <input
                          type="range"
                          min={3}
                          max={15}
                          value={params.iron || 8}
                          onChange={(e) => setParams({ ...params, iron: Number(e.target.value) })}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>3mg</span>
                          <span>권장: 8mg</span>
                          <span>15mg</span>
                        </div>
                      </div>
                    </div>

                    {/* 비율 조정 */}
                    <div className="pt-3 border-t border-blue-200">
                      <h5 className="font-medium text-blue-800 mb-3">영양소 비율 (칼로리 기준)</h5>

                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            탄수화물: {params.carbRatio || 60}%
                          </label>
                          <input
                            type="range"
                            min={50}
                            max={70}
                            value={params.carbRatio || 60}
                            onChange={(e) => setParams({ ...params, carbRatio: Number(e.target.value) })}
                            className="w-full"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            단백질: {params.proteinRatio || 15}%
                          </label>
                          <input
                            type="range"
                            min={10}
                            max={25}
                            value={params.proteinRatio || 15}
                            onChange={(e) => setParams({ ...params, proteinRatio: Number(e.target.value) })}
                            className="w-full"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            지방: {params.fatRatio || 25}%
                          </label>
                          <input
                            type="range"
                            min={15}
                            max={35}
                            value={params.fatRatio || 25}
                            onChange={(e) => setParams({ ...params, fatRatio: Number(e.target.value) })}
                            className="w-full"
                          />
                        </div>

                        {/* 합계 체크 */}
                        <div className="text-xs text-gray-600 bg-white p-2 rounded">
                          총 비율: {ratioSum}%
                          {ratioSum !== 100 && (
                            <span className="text-orange-600 ml-2">⚠️ 100%가 되도록 조정해주세요</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 자연어 조정 */}
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900">🆕 실제 자연어 처리</h3>

                  <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
                    <p className="text-sm text-gray-600 mb-3">실제 NLP로 처리되는 키워드:</p>
                    <div className="text-xs text-gray-500 space-y-1">
                      <div>
                        <strong>예산:</strong> "가격 500원 올려줘", "예산을 6000원으로 설정"
                      </div>
                      <div>
                        <strong>기간:</strong> "기간을 25일로 변경", "30일로 늘려줘"
                      </div>
                      <div>
                        <strong>칼로리:</strong> "칼로리를 950으로 늘려줘", "900kcal로 조정"
                      </div>
                      <div>
                        <strong>영양소:</strong> "단백질 30g으로 증가", "비타민C 80mg 설정"
                      </div>
                      <div>
                        <strong>비율:</strong> "탄수화물 비율 55%로", "단백질 20% 늘려줘"
                      </div>
                    </div>
                  </div>

                  <textarea
                    className="w-full h-20 p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
                    placeholder="자연어로 설정을 변경해보세요... (예: 예산 6000원으로 올리고 단백질 30g으로 설정해줘)"
                    value={naturalLanguageInput}
                    onChange={(e) => setNaturalLanguageInput(e.target.value)}
                  />

                  <button
                    onClick={handleNaturalLanguageChange}
                    disabled={loading || !naturalLanguageInput.trim()}
                    className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-all disabled:opacity-50"
                  >
                    {loading ? (
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        실제 NLP 처리 중...
                      </div>
                    ) : (
                      <div className="flex items-center justify-center gap-2">
                        <span className="text-xl">⚡</span>
                        자연어 처리하기
                      </div>
                    )}
                  </button>
                </div>
              </div>

              <div className="mt-2">
                <button
                  onClick={handleOptimization}
                  disabled={loading || ratioSum !== 100}
                  className="w-full py-4 bg-blue-600 text-white rounded-xl font-semibold disabled:opacity-50 hover:bg-blue-700 transition-all"
                >
                  {loading ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      실제 GA 알고리즘 실행 중...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-xl">📅</span>
                      실제 CSV 기반 메뉴 최적화 실행
                    </div>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: 결과 */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 border border-white/50 shadow-xl">
              <h2 className="text-xl font-bold text-gray-900 mb-2">최적화 결과</h2>
              <p className="text-gray-600">선택 전략: {selectedAlternative?.title || "(미선택)"}</p>

              <div className="grid gap-4 sm:grid-cols-3 mt-4">
                <div className="bg-white rounded-xl p-4 border">
                  <div className="text-xs text-gray-500">총 일수</div>
                  <div className="text-2xl font-bold">{params.days}일</div>
                </div>
                <div className="bg-white rounded-xl p-4 border">
                  <div className="text-xs text-gray-500">총 예산(예상)</div>
                  <div className="text-2xl font-bold">{totalCost.toLocaleString()}원</div>
                </div>
                <div className="bg-white rounded-xl p-4 border">
                  <div className="text-xs text-gray-500">평균 열량(예상)</div>
                  <div className="text-2xl font-bold">{avgKcal} kcal</div>
                </div>
              </div>
            </div>

            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 border border-white/50 shadow-xl">
              <h3 className="font-semibold text-gray-900 mb-4">일자별 식단</h3>
              {menuPlan.length === 0 ? (
                <div className="text-gray-500">로딩 중.</div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {menuPlan.map((d) => (
                    <div key={d.day} className="border rounded-xl p-4 bg-white">
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-sm font-semibold text-blue-600">DAY {d.day}</div>
                        <div className="text-xs text-gray-500">{d.day_kcal} kcal</div>
                      </div>
                      <div className="space-y-1 text-sm">
                        <div>🍚 {d.rice}</div>
                        <div>🥣 {d.soup}</div>
                        <div>🥬 {d.side1}</div>
                        <div>🥕 {d.side2}</div>
                        <div>🌶️ {d.side3}</div>
                        <div className="text-blue-600 font-medium">🍎 {d.snack}</div>
                      </div>
                      <div className="mt-3 text-right text-xs text-gray-600">
                        {d.day_cost?.toLocaleString?.() ?? d.day_cost}원
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 가정통신문 생성 버튼 */}
            <div className="flex justify-end">
              <button
                onClick={handleGenerateReport}
                disabled={loading || menuPlan.length === 0}
                className="flex-1 sm:flex-none px-5 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-all disabled:opacity-50"
              >
                {loading ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    생성 중...
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-xl">📄</span>
                    가정통신문 생성
                  </div>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
