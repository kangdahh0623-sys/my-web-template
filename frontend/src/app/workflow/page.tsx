"use client";

import React, { useMemo, useState } from "react";
import { useRouter } from 'next/navigation';
import { 
  generateWorkflowAlternatives, 
  analyzeWithAgents, 
  parseNaturalLanguage,  // 추가
  optimizeWithStrategy,
  type WorkflowAlternative,
  type AgentAnalysis,
  type PlanRow 
} from '@/lib/api';

// Types
interface Alternative {
  id: number;
  title: string;
  description: string;
  estimated_cost: number;
  target_calories: number;
  features?: string[];
  highlight?: string;
}

interface MenuRow {
  day: number;
  rice: string;
  soup: string;
  side1: string;
  side2: string;
  side3: string;
  snack: string;
  day_cost: number;
  day_kcal: number;
}

export default function WorkflowPage() {
      const [error, setError] = useState<string | null>(null);
      const router = useRouter();
  // Step state
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Step 1: user prompt
  const [userRequest, setUserRequest] = useState<string>(
    "예산 5370원으로 20일치 영양가 높은 급식 메뉴를 계획해주세요"
  );

  // Generic loading flag
  const [loading, setLoading] = useState<boolean>(false);

  // Step 2: alternatives
  const [alternatives, setAlternatives] = useState<Alternative[]>([]);
  const [selectedAlternativeId, setSelectedAlternativeId] = useState<number | null>(null);

  // Step 3: params
  const [params, setParams] = useState<Record<string, number>>({ days: 20, budget: 5370, calories: 900 });
  const [naturalLanguageInput, setNaturalLanguageInput] = useState<string>("");

  // (Optional) Agent analysis placeholder (kept nullable so UI still renders)
  const [agentAnalysis] = useState<
    | null
    | {
        nutrition_agent: number;
        economic_agent: number;
        student_agent: number;
        operation_agent: number;
        consensus: string;
        recommendation: string;
      }
  >(null);

  // Step 4: result
  const [menuPlan, setMenuPlan] = useState<MenuRow[]>([]);

  const steps = [
    { num: 1, title: "사용자 입력", icon: "👤" },
    { num: 2, title: "AI 대안 생성", icon: "✨" },
    { num: 3, title: "설정 조정", icon: "⚙️" },
    { num: 4, title: "메뉴 최적화", icon: "📅" },
  ];

  const mockAlternatives: Alternative[] = [
    {
      id: 1,
      title: "영양 균형 중심 전략",
      description: "단백질, 비타민, 무기질의 완벽한 균형을 맞춘 성장기 학생 맞춤 식단",
      estimated_cost: 5200,
      target_calories: 920,
      features: ["고단백 식품", "비타민 A,C 강화", "칼슘/철분 최적화"],
      highlight: "영양소 완전 균형",
    },
    {
      id: 2,
      title: "경제성 우선 전략",
      description: "예산 내에서 최대한 다양하고 풍성한 메뉴를 제공하는 실용적 접근",
      estimated_cost: 4850,
      target_calories: 880,
      features: ["예산 절약", "메뉴 다양성", "대용량 조리"],
      highlight: "비용 효율성",
    },
    {
      id: 3,
      title: "선호도 중심 전략",
      description: "학생 기호도 조사를 바탕으로 한 높은 만족도와 섭취율을 목표로 하는 식단",
      estimated_cost: 5100,
      target_calories: 950,
      features: ["학생 선호 메뉴", "높은 섭취율", "트렌디한 퓨전"],
      highlight: "학생 만족도",
    },
  ];

  const selectedAlternative = useMemo(
    () => alternatives.find((a) => a.id === selectedAlternativeId) || null,
    [alternatives, selectedAlternativeId]
  );

  // Handlers
  async function handleGenerateAlternatives() {
    setLoading(true);
    // Mock
    setTimeout(() => {
      setAlternatives(mockAlternatives);
      setCurrentStep(2);
      setLoading(false);
    }, 800);
  }

  async function handleSelectAlternative(id: number) {
    setSelectedAlternativeId(id);
    setLoading(true);
    setTimeout(() => {
      setCurrentStep(3);
      setLoading(false);
    }, 500);
  }

  function parseKoreanNumber(str: string): number | null {
    const n = parseInt(str.replace(/[^0-9]/g, ""), 10);
    return Number.isFinite(n) ? n : null;
  }


  const handleNaturalLanguageChange = async () => {
    if (!naturalLanguageInput.trim()) {
        setError("변경할 내용을 입력해주세요.");
        return;
    }

  setLoading(true);
  setError(null);
  
  try {
    console.log("🗣️ 자연어 파싱 시작:", naturalLanguageInput);
    console.log("현재 파라미터:", params);
    
    // 실제 API 호출
    const result = await parseNaturalLanguage(naturalLanguageInput, params);
    
    console.log("✅ 파라미터 변경 완료:", result);
    
    // 파라미터 업데이트 (changes 제외하고 나머지만)
    const { changes, ...newParams } = result;
    setParams(newParams);
    setNaturalLanguageInput("");
    
    // 변경사항 알림
    if (changes && changes.length > 0) {
      alert(`변경 완료:\n${changes.join('\n')}`);
    } else {
      alert("인식된 변경사항이 없습니다. 다른 표현으로 시도해보세요.");
    }
    
  } catch (e: any) {
    console.error("❌ 자연어 파싱 실패:", e);
    setError(e.message || "자연어 처리 중 오류가 발생했습니다.");
  } finally {
    setLoading(false);
  }
};

  async function handleOptimization() {
    setLoading(true);
    setCurrentStep(4);

    // Mock GA result
    setTimeout(() => {
      const mock: MenuRow[] = Array.from({ length: params.days }, (_, i) => ({
        day: i + 1,
        rice: i % 3 === 0 ? "잡곡밥" : "현미밥",
        soup: ["김치찌개", "된장국", "미역국"][i % 3],
        side1: ["불고기", "생선구이", "닭갈비"][i % 3],
        side2: ["시금치나물", "콩나물무침"][i % 2],
        side3: ["김치", "깍두기"][i % 2],
        snack: i % 7 === 2 ? "사과" : "(없음)",
        day_cost: Math.floor(Math.random() * 1000 + 4500),
        day_kcal: Math.floor(Math.random() * 200 + 800),
      }));
      setMenuPlan(mock);
      setLoading(false);
    }, 900);
  }

  const ratioSum = (params.carbRatio || 60) + (params.proteinRatio || 15) + (params.fatRatio || 25);

  const totalCost = useMemo(() => menuPlan.reduce((acc, r) => acc + r.day_cost, 0), [menuPlan]);
  const avgKcal = useMemo(
    () => (menuPlan.length ? Math.round(menuPlan.reduce((a, r) => a + r.day_kcal, 0) / menuPlan.length) : 0),
    [menuPlan]
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-green-50 to-blue-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 
            className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-green-600 bg-clip-text text-transparent cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => router.push('/')}
          >
            🍽️ 급식 메뉴 최적화 시스템
          </h1>

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
                    selectedAlternativeId === alt.id ? "border-blue-500 bg-blue-50 shadow-lg" : "border-gray-200 bg-white hover:border-blue-300"
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
                      <span className="font-semibold text-green-600">{alt.estimated_cost.toLocaleString()}원</span>
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
            {/* Agent-based 분석 (옵션) */}
            {agentAnalysis && (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="text-xl">🤖</span>
                  실제 CSV 기반 Multi-Agent 분석 결과
                </h3>

                <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl p-6">
                  <h4 className="font-semibold text-gray-900 mb-3">선택된 전략: {selectedAlternative?.title}</h4>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{agentAnalysis.nutrition_agent.toFixed(0)}</div>
                      <div className="text-sm text-gray-600">🥗 영양사 에이전트</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-700">{agentAnalysis.economic_agent.toFixed(0)}</div>
                      <div className="text-sm text-gray-600">💰 경제 에이전트</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-800">{agentAnalysis.student_agent.toFixed(0)}</div>
                      <div className="text-sm text-gray-600">😊 학생 에이전트</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-900">{agentAnalysis.operation_agent.toFixed(0)}</div>
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

            {/* 설정 조정 */}
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
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900">실시간 설정 조정</h3>

                  {/* 기본 설정 */}
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
                      <label className="block text-sm font-medium text-gray-700 mb-2">목표 칼로리: {params.calories}kcal</label>
                      <input
                        type="number"
                        value={params.calories}
                        onChange={(e) => setParams({ ...params, calories: Number(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  {/* 영양성분 조정 */}
                  <div className="bg-blue-50 rounded-xl p-4 space-y-4">
                    <h4 className="font-medium text-blue-800">영양성분 목표 조정</h4>

                    <div className="grid grid-cols-1 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">단백질: {params.protein || 25}g</label>
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
                        <label className="block text-sm font-medium text-gray-700 mb-2">비타민C: {params.vitaminC || 50}mg</label>
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
                        <label className="block text-sm font-medium text-gray-700 mb-2">칼슘: {params.calcium || 400}mg</label>
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
                        <label className="block text-sm font-medium text-gray-700 mb-2">철분: {params.iron || 8}mg</label>
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

                    {/* 영양소 비율 조정 */}
                    <div className="pt-3 border-t border-blue-200">
                      <h5 className="font-medium text-blue-800 mb-3">영양소 비율 (칼로리 기준)</h5>

                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">탄수화물: {params.carbRatio || 60}%</label>
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
                          <label className="block text-sm font-medium text-gray-700 mb-2">단백질: {params.proteinRatio || 15}%</label>
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
                          <label className="block text-sm font-medium text-gray-700 mb-2">지방: {params.fatRatio || 25}%</label>
                          <input
                            type="range"
                            min={15}
                            max={35}
                            value={params.fatRatio || 25}
                            onChange={(e) => setParams({ ...params, fatRatio: Number(e.target.value) })}
                            className="w-full"
                          />
                        </div>

                        {/* 비율 합계 체크 */}
                        <div className="text-xs text-gray-600 bg-white p-2 rounded">
                          총 비율: {ratioSum}%
                          {ratioSum !== 100 && <span className="text-orange-600 ml-2">⚠️ 100%가 되도록 조정해주세요</span>}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 자연어 조정 */}
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900">🆕 실제 자연어 처리</h3>

                  {/* 자연어 키워드 가이드 */}
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
                <div className="text-gray-500">결과가 아직 없습니다.</div>
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
                      <div className="mt-3 text-right text-xs text-gray-600">{d.day_cost.toLocaleString()}원</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
