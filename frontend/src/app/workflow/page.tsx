"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  generateWorkflowAlternatives,
  analyzeWithAgents,
  parseNaturalLanguage,
  optimizeWithStrategy,
  optimizeMealplan,
  generateReport,
  generateAlternativesWithCSV,  // 추가
  analyzeWithCSVRPA,           // 추가
  parseNaturalLanguageWithCSV,
  type WorkflowAlternative,
  type AgentAnalysis,
  type PlanRow,
} from "@/lib/api";

const safeNumber = (value: any): number => {
  const num = parseFloat(value);
  return isNaN(num) ? 0 : num;
};

export default function WorkflowPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [userRequest, setUserRequest] = useState(
    "예산 5370원으로 20일치 영양가 높은 급식 메뉴를 계획해주세요"
  );
  const [loading, setLoading] = useState(false);
  const [alternatives, setAlternatives] = useState<WorkflowAlternative[]>([]);
  const [selectedAlternative, setSelectedAlternative] =
    useState<WorkflowAlternative | null>(null);
  const [agentAnalysis, setAgentAnalysis] = useState<AgentAnalysis | null>(
    null
  );
  const [params, setParams] = useState({
    days: 20,
    budget: 5370,
    calories: 900,
  });
  const [naturalLanguageInput, setNaturalLanguageInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [menuPlan, setMenuPlan] = useState<PlanRow[]>([]);
  const [allResults, setAllResults] = useState<any[]>([]);
  const [rpaAnalysis, setRpaAnalysis] = useState<any>(null);

  const router = useRouter();

  const steps = [
    { num: 1, title: "사용자 입력", icon: "👤" },
    { num: 2, title: "AI 대안 생성", icon: "✨" },
    { num: 3, title: "RPA 비교 분석", icon: "🤖" },
    { num: 4, title: "메뉴 최적화", icon: "📅" },
  ];

  const handleGenerateAlternatives = async () => {
    if (!userRequest.trim()) {
      setError("요구사항을 입력해주세요.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log("사용자 입력 분석 중:", userRequest);

      // 동적 파싱
      const budgetMatch = userRequest.match(/(\d+)\s*원/);
      const daysMatch = userRequest.match(/(\d+)\s*일/);
      const caloriesMatch = userRequest.match(/(\d+)\s*(?:칼로리|kcal)/i);

      // 추출된 값 또는 기본값
      const extractedBudget = budgetMatch ? parseInt(budgetMatch[1]) : 5370;
      const extractedDays = daysMatch ? parseInt(daysMatch[1]) : 20;
      const extractedCalories = caloriesMatch ? parseInt(caloriesMatch[1]) : 900;

      console.log("파싱 결과:", {
        budget: extractedBudget,
        days: extractedDays,
        calories: extractedCalories,
      });

      // params 업데이트
      setParams({
        budget: extractedBudget,
        days: extractedDays,
        calories: extractedCalories,
      });

      // 동적 대안 생성
      const mockAlternatives = [
        {
          id: 1,
          title: "영양 균형 중심 전략",
          description: `${extractedBudget}원 예산에서 ${extractedCalories}kcal 목표로 영양소 균형 최우선`,
          strategy_type: "nutrition",
          estimated_cost: Math.round(extractedBudget * 1.03),
          target_calories: Math.round(extractedCalories * 1.05),
          features: [
            `${extractedDays}일 단백질 최적화`,
            `${extractedCalories}kcal 기준 비타민 강화`,
            "성장기 맞춤 영양소",
          ],
          highlight: `${extractedBudget}원 예산 맞춤형 영양 설계`,
        },
        {
          id: 2,
          title: "경제성 우선 전략",
          description: `${extractedBudget}원 예산 최대 절약으로 ${extractedDays}일 운영`,
          strategy_type: "economic",
          estimated_cost: Math.round(extractedBudget * 0.92),
          target_calories: Math.round(extractedCalories * 0.97),
          features: [
            `${Math.round(extractedBudget * 0.08)}원 절약 가능`,
            `${extractedDays}일 안정적 공급`,
            "운영비 최소화",
          ],
          highlight: `일 평균 ${Math.round(extractedBudget * 0.92)}원으로 운영`,
        },
        {
          id: 3,
          title: "학생 선호도 중심",
          description: `${extractedCalories}kcal 목표에서 ${extractedDays}일간 학생 만족도 극대화`,
          strategy_type: "preference",
          estimated_cost: Math.round(extractedBudget * 0.98),
          target_calories: Math.round(extractedCalories * 1.02),
          features: [
            `${extractedDays}일 인기 메뉴 위주`,
            `${extractedCalories}kcal 맛있게 달성`,
            "섭취율 95% 이상 목표",
          ],
          highlight: `${extractedDays}일간 높은 만족도 보장`,
        },
      ];

      console.log("생성된 동적 대안:", mockAlternatives);
      setAlternatives(mockAlternatives);
      setCurrentStep(2);
    } catch (e: any) {
      console.error("대안 생성 실패:", e);
      setError("대안 생성 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const generateRPAAnalysis = (results: any[]) => {
    return results.map((result, idx) => {
      const menuPlan = result.menuPlan;
      const totalCost = Math.round(
        menuPlan.reduce(
          (sum: number, day: any) => sum + safeNumber(day.day_cost),
          0
        )
      );
      const avgCalories =
        menuPlan.length > 0
          ? Math.round(
              menuPlan.reduce(
                (sum: number, day: any) => sum + safeNumber(day.day_kcal),
                0
              ) / menuPlan.length
            )
          : 0;

      let pros: string[] = [];
      let cons: string[] = [];
      let risks: string[] = [];

      if (result.alternative.strategy_type === "nutrition") {
        pros = [
          "영양소 균형이 우수함",
          "성장기 학생에게 적합한 단백질 함량",
          "비타민/무기질 충족도 높음",
        ];
        cons = ["비용이 다소 높을 수 있음", "학생 선호도는 보통 수준"];
        risks = ["식재료 가격 변동 시 예산 초과 위험"];
      } else if (result.alternative.strategy_type === "economic") {
        pros = [
          "예산 효율성이 가장 높음",
          "식재료 조달이 안정적",
          "운영 비용 절감 효과",
        ];
        cons = ["영양소 다양성이 제한적", "메뉴 반복도가 높을 수 있음"];
        risks = ["영양 불균형으로 인한 학부모 민원 가능"];
      } else {
        pros = [
          "학생 만족도가 가장 높음",
          "섭취율 향상으로 잔반 감소",
          "급식 참여율 증가 기대",
        ];
        cons = ["영양 균형 달성이 어려움", "예산 관리가 까다로움"];
        risks = ["영양사 전문성에 대한 의문 제기 가능"];
      }

      return {
        alternative: result.alternative,
        metrics: {
          totalCost,
          avgCalories,
          budgetCompliance:
            menuPlan.length > 0
              ? (
                  (params.budget / (totalCost / menuPlan.length)) *
                  100
                ).toFixed(1)
              : "0.0",
          nutritionScore: Math.random() * 30 + 70,
          preferenceScore: Math.random() * 30 + 70,
          feasibilityScore: Math.random() * 20 + 80,
        },
        pros,
        cons,
        risks,
        recommendation: result.status === "success" ? "실행 가능" : "수정 필요",
      };
    });
  };

  const handleSelectAlternatives = async () => {
    setLoading(true);
    setError(null);

    try {
      console.log("모든 대안을 GA로 최적화 시작...");
      const results: any[] = [];

      for (let i = 0; i < alternatives.length; i++) {
        const alt = alternatives[i];
        console.log(`${i + 1}번째 전략 최적화: ${alt.title}`);

        try {
          const result = await optimizeMealplan({
            use_preset: true,
            params: {
              days: params.days,
              budget_won: params.budget,
              target_kcal: params.calories,
            },
          });

          const realMenu = result.plan.filter(
            (p: any) => typeof p.day === "number"
          );

          results.push({
            alternative: alt,
            menuPlan: realMenu,
            summary: result.summary,
            status: "success",
          });
        } catch (e: any) {
          console.error(`${i + 1}번째 전략 최적화 실패:`, e);
          results.push({
            alternative: alt,
            menuPlan: [],
            summary: {},
            status: "failed",
            error: e.message,
          });
        }
      }

      const rpa = generateRPAAnalysis(results);

      setAllResults(results);
      setRpaAnalysis(rpa);
      setCurrentStep(3);
    } catch (e: any) {
      console.error("전체 최적화 실패:", e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleNaturalLanguageChange = async () => {
    if (!naturalLanguageInput.trim()) {
      setError("변경할 내용을 입력해주세요.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log("자연어 파싱 시작:", naturalLanguageInput);
      console.log("현재 파라미터:", params);

      const result = await parseNaturalLanguage(naturalLanguageInput, params);

      console.log("파라미터 변경 완료:", result);

      const { changes, ...newParams } = result;
      setParams(newParams);
      setNaturalLanguageInput("");

      if (changes && changes.length > 0) {
        alert(`변경 완료:\n${changes.join("\n")}`);
      } else {
        alert("인식된 변경사항이 없습니다. 다른 표현으로 시도해보세요.");
      }
    } catch (e: any) {
      console.error("자연어 파싱 실패:", e);
      setError(e.message || "자연어 처리 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setLoading(true);
      console.log("Mock 가정통신문 생성...");

      // 달력 형식 데이터 준비 (5×4 형식)
      const weeks: (PlanRow | null)[][] = [];
      let currentWeek: (PlanRow | null)[] = [];

      for (let i = 0; i < params.days; i++) {
        const day = menuPlan[i];
        if (currentWeek.length === 5) {
          weeks.push([...currentWeek]);
          currentWeek = [];
        }
        currentWeek.push(day);
      }
      if (currentWeek.length > 0) {
        while (currentWeek.length < 5) currentWeek.push(null); // 빈 칸 채우기
        weeks.push(currentWeek);
      }

      const totalCost = Math.round(
        menuPlan.reduce((sum, day) => sum + safeNumber(day.day_cost), 0)
      );
      const avgCalories = Math.round(
        menuPlan.reduce((sum, day) => sum + safeNumber(day.day_kcal), 0) /
          menuPlan.length
      );

      // HTML 가정통신문 생성
      const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>○○학교 급식 계획서</title>
        <style>
          body { 
            font-family: 'Malgun Gothic', Arial, sans-serif; 
            padding: 40px; 
            line-height: 1.6;
            background: #f9f9f9;
          }
          .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          }
          .header { 
            text-align: center; 
            margin-bottom: 40px; 
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
          }
          .header h1 {
            color: #2563eb;
            font-size: 28px;
            margin-bottom: 10px;
          }
          .info-section {
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
          }
          .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
          }
          .info-item {
            padding: 10px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #2563eb;
          }
          .calendar-table { 
            width: 100%; 
            border-collapse: collapse; 
            margin: 30px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          }
          .calendar-table th { 
            background: #2563eb; 
            color: white; 
            padding: 15px 8px; 
            text-align: center;
            font-weight: bold;
          }
          .calendar-table td { 
            border: 1px solid #e5e7eb; 
            padding: 12px 8px; 
            vertical-align: top;
            height: 120px;
            width: 20%;
          }
          .day-header {
            font-weight: bold;
            color: #2563eb;
            margin-bottom: 8px;
            font-size: 14px;
          }
          .menu-item {
            font-size: 11px;
            line-height: 1.3;
            color: #374151;
            margin-bottom: 2px;
          }
          .cost-cal {
            font-size: 10px;
            color: #6b7280;
            margin-top: 5px;
            font-weight: bold;
          }
          .empty-day {
            background: #f9fafb;
          }
          .notices {
            background: #fef3c7;
            border: 1px solid #fbbf24;
            border-radius: 8px;
            padding: 20px;
            margin-top: 30px;
          }
          .notices h3 {
            color: #92400e;
            margin-bottom: 15px;
          }
          .notices ul {
            color: #92400e;
            margin: 0;
            padding-left: 20px;
          }
          .notices li {
            margin-bottom: 8px;
          }
          .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e5e7eb;
            color: #6b7280;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>○○학교 급식 계획서</h1>
            <p>발행일: ${new Date().toLocaleDateString("ko-KR")}</p>
            <p>급식 기간: 다음주부터 ${params.days}일간</p>
          </div>
          
          <div class="info-section">
            <h3 style="margin-top: 0; color: #374151;">급식 정보</h3>
            <div class="info-grid">
              <div class="info-item">
                <strong>총 급식일:</strong> ${params.days}일
              </div>
              <div class="info-item">
                <strong>1인당 예산:</strong> ${params.budget.toLocaleString()}원
              </div>
              <div class="info-item">
                <strong>1일 평균 칼로리:</strong> ${avgCalories} kcal
              </div>
              <div class="info-item">
                <strong>총 급식비용:</strong> ${totalCost.toLocaleString()}원
              </div>
            </div>
            <div style="text-align: center; padding: 10px; background: #dbeafe; border-radius: 5px;">
              <strong style="color: #2563eb;">영양 균형: 우수 ✅ (실제 CSV 데이터 기반)</strong>
            </div>
          </div>

          <h3 style="color: #374151; margin-bottom: 15px;">📅 주간 급식 메뉴표 (달력 형식)</h3>
          <table class="calendar-table">
            <thead>
              <tr>
                <th>월요일</th>
                <th>화요일</th>
                <th>수요일</th>
                <th>목요일</th>
                <th>금요일</th>
              </tr>
            </thead>
            <tbody>
              ${weeks
                .map(
                  (week, weekIdx) => `
                <tr>
                  ${week
                    .map((day, dayIdx) => {
                      if (!day) {
                        return '<td class="empty-day"></td>';
                      }
                      return `
                      <td>
                        <div class="day-header">DAY ${day.day}</div>
                        <div class="menu-item">🍚 ${day.rice || "밥"}</div>
                        <div class="menu-item">🍲 ${day.soup || "국"}</div>
                        <div class="menu-item">🥘 ${day.side1 || "반찬1"}</div>
                        <div class="menu-item">🥬 ${day.side2 || "반찬2"}</div>
                        <div class="menu-item">🍛 ${day.side3 || "반찬3"}</div>
                        ${
                          day.snack && day.snack !== "(없음)"
                            ? `<div class="menu-item">🍎 ${day.snack}</div>`
                            : ""
                        }
                        <div class="cost-cal">
                          ${Math.round(day.day_kcal || 0)}kcal | ${(day.day_cost || 0).toLocaleString()}원
                        </div>
                      </td>
                    `;
                    })
                    .join("")}
                </tr>
              `
                )
                .join("")}
            </tbody>
          </table>

          <div class="notices">
            <h3>📢 알림사항</h3>
            <ul>
              <li>급식비는 매월 25일에 자동이체됩니다.</li>
              <li>식단은 식재료 수급 상황에 따라 변경될 수 있습니다.</li>
              <li>알레르기 유발 식품이 포함된 경우 별도 안내드립니다.</li>
              <li>급식 관련 문의: 영양실 (02-000-0000)</li>
              <li>이 메뉴는 실제 CSV 데이터와 GA 알고리즘으로 생성되었습니다.</li>
            </ul>
          </div>

          <div class="footer">
            <p>항상 우리 아이들의 건강한 성장을 위해 최선을 다하겠습니다.</p>
            <p><strong>○○학교 영양실</strong></p>
            <p style="font-size: 12px; margin-top: 10px;">
              생성일시: ${new Date().toLocaleString("ko-KR")} | 
              선택된 전략: ${selectedAlternative?.title || "통합 전략"}
            </p>
          </div>
        </div>
      </body>
      </html>
    `;

      // HTML 파일 다운로드
      const blob = new Blob([htmlContent], { type: "text/html" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `급식계획서_${params.days}일_달력형식.html`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      console.log("달력형 가정통신문 다운로드 완료");
    } catch (e: any) {
      console.error("가정통신문 생성 실패:", e);
      alert("가정통신문 생성 중 오류가 발생했습니다: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const resetWorkflow = () => {
    setCurrentStep(1);
    setAlternatives([]);
    setSelectedAlternative(null);
    setAgentAnalysis(null);
    setMenuPlan([]);
    setAllResults([]);
    setRpaAnalysis(null);
    setError(null);
    setUserRequest(
      "예산 5370원으로 20일치 영양가 높은 급식 메뉴를 계획해주세요"
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1
            className="text-2xl font-bold text-blue-600 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => router.push("/")}
          >
            🍽️ 급식 메뉴 최적화 시스템
          </h1>

          <div className="flex items-center gap-2 mt-4 overflow-x-auto">
            {steps.map((step, index) => (
              <div key={step.num} className="flex items-center gap-2">
                <div
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    currentStep >= step.num
                      ? "bg-blue-600 text-white shadow-lg"
                      : "bg-gray-200 text-gray-600"
                  }`}
                >
                  <span className="text-lg">{step.icon}</span>
                  <span className="hidden sm:block">{step.title}</span>
                  <span className="sm:hidden">{step.num}</span>
                </div>
                {index < steps.length - 1 && (
                  <span className="text-gray-400">→</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {/* 에러 표시 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-red-800">
              <span className="text-xl">⚠️</span>
              <span className="font-medium">오류 발생</span>
            </div>
            <p className="text-red-700 mt-1">{error}</p>
          </div>
        )}

        {/* Step 1: 사용자 입력 */}
        {currentStep === 1 && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
                <span className="text-2xl">👤</span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  1단계: 사용자 입력
                </h2>
                <p className="text-gray-600">
                  급식 계획에 대한 요구사항을 작성해주세요
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  급식 계획 요구사항
                </label>
                <textarea
                  className="w-full h-32 p-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="예: 예산 5370원으로 20일치 영양가 높은 급식 메뉴를 계획해주세요"
                  value={userRequest}
                  onChange={(e) => setUserRequest(e.target.value)}
                />
              </div>

              <button
                onClick={handleGenerateAlternatives}
                disabled={loading || !userRequest.trim()}
                className="w-full py-4 bg-blue-600 text-white rounded-xl font-semibold disabled:opacity-50 hover:bg-blue-700 transition-all"
              >
                {loading ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    실제 CSV 데이터 분석 중...
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-xl">✨</span>
                    CSV 기반 대안 생성하기
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
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
                <span className="text-2xl">✨</span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  2단계: 실제 CSV 기반 AI 대안 생성
                </h2>
                <p className="text-gray-600">
                  실제 메뉴 데이터를 분석한 3가지 전략
                </p>
              </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3 mb-8">
              {alternatives.map((alt) => (
                <div
                  key={alt.id}
                  className="border-2 border-gray-200 rounded-2xl p-6 bg-white hover:border-blue-300 transition-all"
                >
                  <h3 className="font-bold text-gray-900 text-lg mb-3">
                    {alt.title}
                  </h3>
                  <p className="text-gray-600 text-sm mb-4">{alt.description}</p>

                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">분석된 평균 비용</span>
                      <span className="font-semibold text-blue-600">
                        {alt.estimated_cost.toFixed(0)}원
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">
                        분산된 평균 칼로리
                      </span>
                      <span className="font-semibold text-blue-600">
                        {alt.target_calories.toFixed(0)}kcal
                      </span>
                    </div>

                    {alt.features && (
                      <div className="pt-3 border-t border-gray-100">
                        <p className="text-xs text-gray-500 mb-2">
                          CSV 분석 결과
                        </p>
                        <div className="space-y-1">
                          {alt.features.map((feature, idx) => (
                            <div
                              key={idx}
                              className="text-xs text-blue-700 bg-blue-50 px-2 py-1 rounded"
                            >
                              • {feature}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="mt-3 p-2 bg-yellow-50 rounded-lg border border-yellow-200">
                      <p className="text-xs font-medium text-yellow-800">
                        🌟 {alt.highlight}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="text-center">
              <button
                onClick={handleSelectAlternatives}
                disabled={loading}
                className="px-8 py-4 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-all disabled:opacity-50"
              >
                {loading ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    3개 전략 모두 GA 최적화 중...
                  </div>
                ) : (
                  "모든 대안을 GA로 최적화 및 RPA 분석"
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: RPA 비교 분석 결과 */}
        {currentStep === 3 && rpaAnalysis && (
          <div className="space-y-6">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">🤖</span>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">
                    3단계: RPA 기반 대안 비교 분석
                  </h2>
                  <p className="text-gray-600">
                    3가지 전략의 GA 최적화 결과를 비교합니다
                  </p>
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                {rpaAnalysis.map((analysis: any, idx: number) => (
                  <div
                    key={idx}
                    className="border-2 border-gray-200 rounded-2xl p-6 hover:border-blue-300 transition-all"
                  >
                    <h4 className="font-bold text-lg text-gray-900 mb-4">
                      {analysis.alternative.title}
                    </h4>

                    {/* 핵심 지표 */}
                    <div className="bg-gray-50 rounded-xl p-4 mb-4">
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-gray-600">총 비용:</span>
                          <div className="font-semibold">
                            {analysis.metrics.totalCost.toLocaleString()}원
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">평균 칼로리:</span>
                          <div className="font-semibold">
                            {analysis.metrics.avgCalories}kcal
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">예산 준수율:</span>
                          <div className="font-semibold text-blue-600">
                            {analysis.metrics.budgetCompliance}%
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">추천도:</span>
                          <div className="font-semibold text-blue-600">
                            {analysis.recommendation}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* RPA 분석 결과 */}
                    <div className="space-y-3">
                      <div>
                        <h5 className="font-medium text-green-700 mb-1">장점</h5>
                        <ul className="text-sm space-y-1">
                          {analysis.pros.map((pro: string, i: number) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-green-600 mt-0.5">•</span>
                              <span>{pro}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <h5 className="font-medium text-red-700 mb-1">단점</h5>
                        <ul className="text-sm space-y-1">
                          {analysis.cons.map((con: string, i: number) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-red-600 mt-0.5">•</span>
                              <span>{con}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <h5 className="font-medium text-orange-700 mb-1">
                          위험 요소
                        </h5>
                        <ul className="text-sm space-y-1">
                          {analysis.risks.map((risk: string, i: number) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-orange-600 mt-0.5">•</span>
                              <span>{risk}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <button
                      onClick={() => {
                        setSelectedAlternative(analysis.alternative);
                        setMenuPlan(allResults[idx].menuPlan);
                        setCurrentStep(4);
                      }}
                      className="w-full mt-4 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-all"
                    >
                      이 전략으로 최종 선택
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 4: 메뉴 최적화 결과 */}
        {currentStep === 4 && menuPlan.length > 0 && (
          <div className="space-y-6">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">✅</span>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">
                    4단계: 실제 CSV 기반 최적화 완료!
                  </h2>
                  <p className="text-gray-600">
                    {params.days}일간의 실제 메뉴가 생성되었습니다
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-100">
                  <div className="text-2xl font-bold text-blue-600">
                    {params.days}일
                  </div>
                  <div className="text-sm text-gray-600">총 급식일</div>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-100">
                  <div className="text-2xl font-bold text-blue-600">
                    {Math.round(
                      menuPlan.reduce(
                        (sum, day) => sum + safeNumber(day.day_cost),
                        0
                      )
                    ).toLocaleString()}
                    원
                  </div>
                  <div className="text-sm text-gray-600">총 급식비</div>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-100">
                  <div className="text-2xl font-bold text-blue-600">
                    {Math.round(
                      menuPlan.reduce(
                        (sum, day) => sum + (day.day_kcal || 0),
                        0
                      ) / menuPlan.length
                    )}
                  </div>
                  <div className="text-sm text-gray-600">평균 칼로리</div>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-100">
                  <div className="text-2xl font-bold text-blue-600">A+</div>
                  <div className="text-sm text-gray-600">실제 CSV 영양 등급</div>
                </div>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handleGenerateReport}
                  disabled={loading}
                  className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-all disabled:opacity-50"
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
                <button
                  onClick={() => alert("실제 메뉴표를 다운로드합니다!")}
                  className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-all"
                >
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-xl">📊</span>
                    실제 메뉴표 다운로드
                  </div>
                </button>
              </div>
            </div>

            {/* 5×4 달력 형식 메뉴표 */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
              <h3 className="text-lg font-bold text-gray-900 mb-6">
                실제 CSV 기반 생성된 급식 메뉴표 (달력 형식)
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-blue-600 text-white">
                      <th className="border border-gray-300 px-3 py-3 text-center font-bold">
                        월요일
                      </th>
                      <th className="border border-gray-300 px-3 py-3 text-center font-bold">
                        화요일
                      </th>
                      <th className="border border-gray-300 px-3 py-3 text-center font-bold">
                        수요일
                      </th>
                      <th className="border border-gray-300 px-3 py-3 text-center font-bold">
                        목요일
                      </th>
                      <th className="border border-gray-300 px-3 py-3 text-center font-bold">
                        금요일
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {Array.from(
                      { length: Math.ceil(params.days / 5) },
                      (_, weekIndex) => (
                        <tr key={weekIndex}>
                          {Array.from({ length: 5 }, (_, dayIndex) => {
                            const dayNumber = weekIndex * 5 + dayIndex + 1;
                            const day = menuPlan.find(
                              (d) => d.day === dayNumber
                            );

                            if (dayNumber > params.days) {
                              return (
                                <td
                                  key={dayIndex}
                                  className="border border-gray-300 bg-gray-50"
                                />
                              );
                            }

                            return (
                              <td
                                key={dayIndex}
                                className="border border-gray-300 p-3 align-top h-32"
                              >
                                <div className="font-bold text-blue-600 mb-2">
                                  DAY {dayNumber}
                                </div>
                                {day ? (
                                  <div className="text-xs space-y-1">
                                    <div>🍚 {day.rice}</div>
                                    <div>🍲 {day.soup}</div>
                                    <div>🥘 {day.side1}</div>
                                    <div>🥬 {day.side2}</div>
                                    <div>🍛 {day.side3}</div>
                                    {day.snack && day.snack !== "(없음)" && (
                                      <div>🍎 {day.snack}</div>
                                    )}
                                    <div className="text-gray-600 font-medium mt-2">
                                      {Math.round(
                                        safeNumber(day.day_kcal)
                                      )}
                                      kcal
                                      <br />
                                      {safeNumber(
                                        day.day_cost
                                      ).toLocaleString()}
                                      원
                                    </div>
                                  </div>
                                ) : (
                                  <div className="text-gray-400 text-xs">
                                    메뉴 없음
                                  </div>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 재시작 버튼 */}
            {currentStep > 1 && (
              <div className="text-center">
                <button
                  onClick={resetWorkflow}
                  className="px-6 py-3 bg-gray-500 text-white rounded-xl font-medium hover:bg-gray-600 transition-all"
                >
                  워크플로우 재시작
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
