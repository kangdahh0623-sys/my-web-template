"use client";

import { useState } from "react";
import { analyzeBeforeAfter, optimizeMealplan, toMediaUrl, type PlanRow } from "@/lib/api";

// 타입 정의 (실제 api.ts에서 가져와야 함)
interface IntakeResult {
  vis_before: string;
  vis_after: string;
  totals?: {
    kcal?: number;
    protein?: number;
    fat?: number;
    carbo?: number;
    carbohydrate?: number;
    g_intake?: number;
    vitA?: number;
    vit_a?: number;
    thiamin?: number;
    riboflavin?: number;
    niacin?: number;
    vitC?: number;
    vit_c?: number;
    vitD?: number;
    vit_d?: number;
    calcium?: number;
    iron?: number;
  };
}

type ModalType = "student" | "nutritionist" | "auth" | null;
type AuthMode = "login" | "signup";

// 샘플 데이터
const statsData = [
  { label: "전국 학교", value: "11,372", unit: "개교", icon: "🏫", color: "from-blue-500 to-blue-600" },
  { label: "급식 학생", value: "545만", unit: "명", icon: "👨‍🎓", color: "from-green-500 to-green-600" },
  { label: "일평균 급식비", value: "4,850", unit: "원", icon: "💰", color: "from-purple-500 to-purple-600" },
  { label: "영양사", value: "8,240", unit: "명", icon: "👩‍⚕️", color: "from-orange-500 to-orange-600" },
];

const newsData = [
  {
    title: "AI 기반 급식 영양 분석 시스템 도입",
    summary: "사진 촬영만으로 섭취량과 영양소를 분석하는 혁신 기술이 주목받고 있습니다.",
    date: "2024.09.15",
    category: "기술",
    color: "bg-blue-100 text-blue-800"
  },
  {
    title: "학교급식 만족도 90% 돌파",
    summary: "맛있는 급식으로 화제가 된 학교들이 늘어나고 있으며, SNS 인증샷 문화도 확산",
    date: "2024.09.10",
    category: "교육",
    color: "bg-green-100 text-green-800"
  },
  {
    title: "영양사 업무 효율화로 급식 품질 향상",
    summary: "데이터 기반 식단 최적화 시스템으로 영양사들의 업무 부담을 줄이고 있습니다.",
    date: "2024.09.08",
    category: "정책",
    color: "bg-purple-100 text-purple-800"
  },
  {
    title: "저나트륨 급식으로 건강한 식습관 형성",
    summary: "나트륨 저감 정책과 함께 학생들의 건강한 식습관 형성에 기여하고 있습니다.",
    date: "2024.09.05",
    category: "건강",
    color: "bg-orange-100 text-orange-800"
  }
];

const nutritionStandards = [
  { nutrient: "탄수화물", range: "55-65%", current: "62%", color: "bg-green-500" },
  { nutrient: "단백질", range: "7-20%", current: "15%", color: "bg-blue-500" },
  { nutrient: "지방", range: "15-30%", current: "23%", color: "bg-purple-500" },
];

const sidebarMenus = [
  { id: "dashboard", label: "대시보드", icon: "📊" },
  { id: "analysis", label: "식단 분석", icon: "🔍" },
  { id: "nutrition", label: "영양 관리", icon: "🥗" },
  { id: "meal-plan", label: "식단표", icon: "📋" },
  { id: "statistics", label: "통계", icon: "📈" },
  { id: "settings", label: "설정", icon: "⚙️" },
];

export default function HomePage() {
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<{name: string; email: string} | null>(null);

  // Student Modal States
  const [before, setBefore] = useState<File | null>(null);
  const [after, setAfter] = useState<File | null>(null);
  const [tray, setTray] = useState<"high" | "middle">("middle");
  const [studentLoading, setStudentLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<IntakeResult | null>(null);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");

  // Nutritionist Modal States
  const [days, setDays] = useState(20);
  const [budget, setBudget] = useState(5370);
  const [targetKcal, setTargetKcal] = useState(900);
  const [nutritionistLoading, setNutritionistLoading] = useState(false);
  const [plan, setPlan] = useState<PlanRow[]>([]);
  const [detail, setDetail] = useState<PlanRow | null>(null);

  const closeModal = () => {
    setActiveModal(null);
    // Reset states when closing
    setBefore(null);
    setAfter(null);
    setAnalysisResult(null);
    setRating(0);
    setComment("");
    setPlan([]);
    setDetail(null);
  };

  const handleLogin = (email: string, password: string) => {
    // 임시 로그인 로직
    setUser({ name: email.split('@')[0], email });
    setIsLoggedIn(true);
    setActiveModal(null);
  };

  const handleSignup = (name: string, email: string, password: string) => {
    // 임시 회원가입 로직
    setUser({ name, email });
    setIsLoggedIn(true);
    setActiveModal(null);
  };

  const handleLogout = () => {
    setUser(null);
    setIsLoggedIn(false);
  };

  const handleStudentAnalysis = async () => {
    if (!before || !after) return alert("전/후 이미지를 모두 선택하세요.");
    try {
      setStudentLoading(true);
      const result = await analyzeBeforeAfter(before, after, { tray_type: tray });
      setAnalysisResult(result);
    } catch (e: any) {
      console.error("Analysis error:", e);
      alert(e?.message || "분석 실패");
    } finally {
      setStudentLoading(false);
    }
  };

  const handleNutritionistOptimize = async () => {
    if (!isLoggedIn) {
      alert("로그인이 필요한 서비스입니다.");
      setActiveModal("auth");
      return;
    }

    setNutritionistLoading(true);
    try {
      const res = await optimizeMealplan({
        use_preset: true,
        params: { days, budget_won: budget, target_kcal: targetKcal },
      });
      
      // API 응답 구조 확인 및 안전한 처리
      if (res && res.plan) {
        const rows = Array.isArray(res.plan) 
          ? res.plan.filter((p: any) => p && typeof p.day === "number")
          : [];
        setPlan(rows);
        setDetail(null);
        
        if (rows.length === 0) {
          alert("생성된 식단표가 없습니다. 조건을 다시 확인해주세요.");
        }
      } else {
        throw new Error("Invalid response format");
      }
    } catch (e: any) {
      console.error("Optimization error:", e);
      
      // 다양한 에러 상황 처리
      let errorMessage = "식단표 생성 실패";
      
      if (e.name === "AbortError" || e.message?.includes("aborted")) {
        errorMessage = "요청이 중단되었습니다. 네트워크 연결을 확인하고 다시 시도해주세요.";
      } else if (e.message?.includes("fetch")) {
        errorMessage = "서버와 연결할 수 없습니다. 잠시 후 다시 시도해주세요.";
      } else if (e.message) {
        errorMessage = e.message;
      }
      
      alert(errorMessage);
    } finally {
      setNutritionistLoading(false);
    }
  };

  const TARGETS = { kcal: 900, carbo: 100, protein: 25, fat: 25 };

  const Bar = ({ label, value = 0, max, unit = "" }: { label: string; value?: number; max: number; unit?: string }) => {
    const v = Number(value) || 0;
    const m = Math.max(1, Number(max) || 1);
    const pct = Math.max(0, Math.min(100, Math.round((v / m) * 100)));
    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm font-medium text-gray-700">
          <span>{label}</span>
          <span>{v.toFixed(1)} / {m} {unit}</span>
        </div>
        <div className="h-3 w-full rounded-full bg-gradient-to-r from-gray-200 to-gray-300 overflow-hidden">
          <div 
            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-700 ease-out" 
            style={{ width: `${pct}%` }} 
          />
        </div>
      </div>
    );
  };

  const get = (k: string, alt?: string) =>
    (analysisResult?.totals as any)?.[k] ?? (alt ? (analysisResult?.totals as any)?.[alt] : 0) ?? 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors lg:hidden"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                급식줍쇼
              </h1>
            </div>

            <div className="flex items-center gap-4">
              {isLoggedIn && user ? (
                <div className="flex items-center gap-4">
                  <div className="hidden sm:block text-sm">
                    <div className="font-medium text-gray-900">{user.name}님</div>
                    <div className="text-gray-500">{user.email}</div>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                  <button
                    onClick={handleLogout}
                    className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
                  >
                    로그아웃
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {setActiveModal("auth"); setAuthMode("login");}}
                    className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
                  >
                    로그인
                  </button>
                  <button
                    onClick={() => {setActiveModal("auth"); setAuthMode("signup");}}
                    className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all"
                  >
                    회원가입
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 lg:translate-x-0 lg:static lg:inset-0`}>
        <div className="flex h-full w-64 flex-col bg-white/95 backdrop-blur-sm border-r border-gray-200">
          <div className="flex items-center justify-between p-6 lg:hidden">
            <h2 className="text-lg font-semibold text-gray-900">메뉴</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <nav className="flex-1 p-4 space-y-2">
            {sidebarMenus.map((menu) => (
              <button
                key={menu.id}
                className="w-full flex items-center gap-3 px-4 py-3 text-left text-gray-700 hover:bg-gray-100 hover:text-gray-900 rounded-lg transition-all duration-200 group"
              >
                <span className="text-xl group-hover:scale-110 transition-transform">{menu.icon}</span>
                <span className="font-medium">{menu.label}</span>
              </button>
            ))}
          </nav>
          
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                📧
              </div>
              <div className="text-sm">
                <div className="font-medium text-gray-900">고객지원</div>
                <div className="text-gray-500">help@급식줍쇼.kr</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <div className="lg:ml-64">
        {/* Hero Section with Top CTA */}
        <div className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-green-600/10"></div>
          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
            <div className="text-center">
              <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mb-6">
                <span className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse"></span>
                AI 기반 급식 관리 솔루션
              </div>
              <h1 className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-green-600 bg-clip-text text-transparent mb-6">
                급식줍쇼
              </h1>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed mb-12">
                <span className="font-semibold text-blue-600">학생</span>을 위한 스마트 영양 분석과 
                <span className="font-semibold text-green-600"> 영양사</span>를 위한 데이터 기반 식단 최적화를 제공합니다
              </p>
              
              {/* Top Action Cards */}
              <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto mb-20">
                <div 
                  onClick={() => setActiveModal("student")}
                  className="group relative p-8 bg-white/80 backdrop-blur-sm rounded-3xl border border-white/50 shadow-xl hover:shadow-2xl transition-all duration-300 cursor-pointer hover:scale-105 hover:bg-white/90"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 rounded-3xl"></div>
                  <div className="relative">
                    <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                      <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">식단 분석 · 영양</h3>
                    <p className="text-gray-600 leading-relaxed mb-4">
                      전/후 사진으로 섭취량을 분석하고<br/>
                      개인별 영양 상태를 확인해보세요
                    </p>
                    <div className="flex items-center text-sm text-blue-600 font-medium">
                      <span>무료 분석 시작</span>
                      <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>

                <div 
                  onClick={() => setActiveModal("nutritionist")}
                  className="group relative p-8 bg-white/80 backdrop-blur-sm rounded-3xl border border-white/50 shadow-xl hover:shadow-2xl transition-all duration-300 cursor-pointer hover:scale-105 hover:bg-white/90"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-emerald-500/5 rounded-3xl"></div>
                  <div className="relative">
                    <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                      <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                      </svg>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">영양사 · 식단표</h3>
                    <p className="text-gray-600 leading-relaxed mb-4">
                      데이터와 물가를 반영한<br/>
                      최적화된 식단표를 생성하세요
                    </p>
                    <div className="flex items-center text-sm text-green-600 font-medium">
                      <span>식단표 생성하기</span>
                      <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 통계 섹션 */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">대한민국 학교급식 현황</h2>
            <p className="text-lg text-gray-600">전국 학교급식 통계로 보는 우리의 현재</p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-16">
            {statsData.map((stat, index) => (
              <div key={index} className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 border border-white/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center text-2xl mb-4`}>
                  {stat.icon}
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-1">
                  {stat.value}<span className="text-lg text-gray-600">{stat.unit}</span>
                </div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* 영양 기준 섹션 */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-lg mb-16">
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">학교급식 영양 기준</h3>
              <p className="text-gray-600">교육부 고시 학교급식 영양소 섭취 기준</p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8">
              {nutritionStandards.map((item, index) => (
                <div key={index} className="text-center">
                  <div className="mb-4">
                    <div className={`w-20 h-20 mx-auto rounded-full ${item.color} flex items-center justify-center text-white font-bold text-lg mb-3`}>
                      {item.current}
                    </div>
                    <h4 className="font-semibold text-gray-900">{item.nutrient}</h4>
                    <p className="text-sm text-gray-600">기준: {item.range}</p>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`${item.color} h-2 rounded-full transition-all duration-700`}
                      style={{ width: `${parseInt(item.current)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 뉴스 섹션 */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">급식 트렌드 & 뉴스</h2>
            <p className="text-lg text-gray-600">학교급식의 최신 동향을 확인하세요</p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8 mb-16">
            {newsData.map((news, index) => (
              <article key={index} className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 border border-white/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02]">
                <div className="flex items-start gap-4">
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${news.color}`}>
                    {news.category}
                  </div>
                  <div className="text-sm text-gray-500">{news.date}</div>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3 mt-4">{news.title}</h3>
                <p className="text-gray-600 leading-relaxed">{news.summary}</p>
                <button className="mt-4 text-blue-600 hover:text-blue-800 font-medium text-sm transition-colors">
                  자세히 보기 →
                </button>
              </article>
            ))}
          </div>
        </div>

        {/* Footer */}
        <footer className="bg-white/80 backdrop-blur-sm border-t border-gray-200 mt-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="grid md:grid-cols-4 gap-8">
              <div className="md:col-span-2">
                <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent mb-4">
                  급식줍쇼
                </h3>
                <p className="text-gray-600 mb-6">
                  AI 기술로 학교급식의 혁신을 이끌어가는 스마트 영양 관리 플랫폼입니다.
                </p>
                <div className="flex gap-4">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600">
                    📧
                  </div>
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center text-green-600">
                    📱
                  </div>
                  <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center text-purple-600">
                    🌐
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 mb-4">서비스</h4>
                <div className="space-y-2 text-gray-600">
                  <div>식단 분석</div>
                  <div>영양 상담</div>
                  <div>식단표 생성</div>
                  <div>데이터 분석</div>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 mb-4">지원</h4>
                <div className="space-y-2 text-gray-600">
                  <div>사용 가이드</div>
                  <div>FAQ</div>
                  <div>고객지원</div>
                  <div>개발자 API</div>
                </div>
              </div>
            </div>
            
            <div className="border-t border-gray-200 mt-12 pt-8 text-center text-gray-500">
              <p>© 2024 급식줍쇼. 모든 권리 보유.</p>
            </div>
          </div>
        </footer>
      </div>

      {/* Auth Modal */}
      {activeModal === "auth" && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md">
            <div className="p-8">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  {authMode === "login" ? "로그인" : "회원가입"}
                </h2>
                <p className="text-gray-600">
                  {authMode === "login" ? "계정에 로그인하세요" : "새 계정을 만드세요"}
                </p>
              </div>

              <AuthForm 
                mode={authMode} 
                onLogin={handleLogin}
                onSignup={handleSignup}
                onClose={closeModal}
              />

              <div className="mt-6 text-center">
                <button
                  onClick={() => setAuthMode(authMode === "login" ? "signup" : "login")}
                  className="text-blue-600 hover:text-blue-800 transition-colors"
                >
                  {authMode === "login" ? "계정이 없으신가요? 회원가입" : "이미 계정이 있으신가요? 로그인"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Student Modal */}
      {activeModal === "student" && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white/95 backdrop-blur-sm border-b px-8 py-6 rounded-t-3xl">
              <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  식단 분석 · 영양
                </h2>
                <button 
                  onClick={closeModal}
                  className="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors flex items-center justify-center group"
                >
                  <svg className="w-5 h-5 text-gray-500 group-hover:text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="p-8 space-y-8">
              {/* Upload Section */}
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-6 border border-blue-100">
                <div className="grid gap-6 lg:grid-cols-3">
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">식판 종류</label>
                    <select
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                      value={tray}
                      onChange={(e) => setTray(e.target.value as "high" | "middle")}
                    >
                      <option value="middle">중등 (28×22cm)</option>
                      <option value="high">고등 (37×29cm)</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">식전 사진</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setBefore(e.target.files?.[0] || null)}
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">식후 사진</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setAfter(e.target.files?.[0] || null)}
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                  </div>
                </div>

                <button
                  onClick={handleStudentAnalysis}
                  disabled={studentLoading || !before || !after}
                  className="w-full mt-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:from-blue-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-[1.02] disabled:hover:scale-100"
                >
                  {studentLoading ? (
                    <div className="flex items-center justify-center gap-3">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      분석 중...
                    </div>
                  ) : "분석하기"}
                </button>
              </div>

              {/* Results */}
              {analysisResult && (
                <>
                  {/* Images and Nutrition Info */}
                  <div className="grid gap-8 lg:grid-cols-3">
                    <div className="lg:col-span-2 grid gap-6 sm:grid-cols-2">
                      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-lg">
                        <h3 className="font-semibold text-lg mb-4 text-gray-900">Before</h3>
                        <img
                          className="w-full rounded-xl border object-cover aspect-square"
                          src={toMediaUrl(analysisResult.vis_before)}
                          alt="before"
                        />
                      </div>

                      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-lg">
                        <h3 className="font-semibold text-lg mb-4 text-gray-900">After</h3>
                        <img
                          className="w-full rounded-xl border object-cover aspect-square"
                          src={toMediaUrl(analysisResult.vis_after)}
                          alt="after"
                        />
                      </div>
                    </div>

                    <div className="bg-gradient-to-br from-gray-50 to-blue-50 rounded-2xl p-6 border border-gray-200">
                      <h3 className="font-semibold text-lg mb-6 text-gray-900">영양 성분</h3>
                      <div className="grid grid-cols-2 gap-4">
                        {[
                          ["g_intake", "섭취량"],
                          ["vitA", "비타민A"],
                          ["thiamin", "티아민"],
                          ["riboflavin", "리보플라빈"],
                          ["niacin", "니아신"],
                          ["vitC", "비타민C"],
                          ["vitD", "비타민D"],
                          ["calcium", "칼슘"],
                          ["iron", "철분"],
                        ].map(([key, label]) => {
                          const val = get(key, key.startsWith("vit") ? key.replace("vit", "vit_").toLowerCase() : undefined);
                          return (
                            <div key={key} className="bg-white rounded-xl p-3 border border-gray-100">
                              <dt className="text-xs font-medium text-gray-500 mb-1">{label}</dt>
                              <dd className="text-sm font-semibold text-gray-900">
                                {typeof val === "number" ? val.toFixed(1) : String(val)}
                              </dd>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  {/* Progress Bars */}
                  <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-lg">
                    <h3 className="font-semibold text-lg mb-6 text-gray-900">총 섭취량 요약</h3>
                    <div className="grid gap-6 sm:grid-cols-2">
                      <Bar label="칼로리" value={analysisResult.totals?.kcal} max={TARGETS.kcal} unit="kcal" />
                      <Bar label="탄수화물" value={get("carbo", "carbohydrate")} max={TARGETS.carbo} unit="g" />
                      <Bar label="단백질" value={analysisResult.totals?.protein} max={TARGETS.protein} unit="g" />
                      <Bar label="지방" value={analysisResult.totals?.fat} max={TARGETS.fat} unit="g" />
                    </div>
                  </div>

                  {/* Review Section */}
                  <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-2xl p-6 border border-yellow-200">
                    <h3 className="font-semibold text-lg mb-4 text-gray-900">오늘 급식 평가</h3>
                    <div className="flex gap-2 text-3xl mb-4">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <button
                          key={i}
                          onClick={() => setRating(i + 1)}
                          className={`transition-all hover:scale-110 ${
                            i < rating ? "text-yellow-400" : "text-gray-300 hover:text-yellow-400"
                          }`}
                        >
                          ★
                        </button>
                      ))}
                    </div>
                    <textarea
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 min-h-[120px] focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all resize-none"
                      placeholder="오늘 급식은 어떠셨나요? 후기를 남겨주세요 😊"
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                    />
                    <div className="flex justify-end mt-4">
                      <button
                        onClick={() => alert(`별점: ${rating}점\n리뷰: ${comment || "(비어있음)"}`)}
                        className="px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-white rounded-xl font-medium hover:from-yellow-600 hover:to-orange-600 transition-all transform hover:scale-105"
                      >
                        평가 저장
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Nutritionist Modal */}
      {activeModal === "nutritionist" && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white/95 backdrop-blur-sm border-b px-8 py-6 rounded-t-3xl">
              <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                  영양사 · 식단표 생성
                </h2>
                <button 
                  onClick={closeModal}
                  className="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors flex items-center justify-center group"
                >
                  <svg className="w-5 h-5 text-gray-500 group-hover:text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="p-8 space-y-8">
              {/* Input Section */}
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border border-green-100">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">식단표 설정</h3>
                <p className="text-sm text-gray-600 mb-6">
                  CSV 경로는 서버 환경변수를 사용합니다. 원하는 조건을 입력해주세요.
                </p>

                <div className="grid sm:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">기간 (일)</label>
                    <input
                      type="number"
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                      value={days}
                      onChange={(e) => setDays(Number(e.target.value || 20))}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">1인 예산 (원)</label>
                    <input
                      type="number"
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                      value={budget}
                      onChange={(e) => setBudget(Number(e.target.value || 0))}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">목표 칼로리 (kcal)</label>
                    <input
                      type="number"
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                      value={targetKcal}
                      onChange={(e) => setTargetKcal(Number(e.target.value || 0))}
                    />
                  </div>
                </div>

                <button
                  onClick={handleNutritionistOptimize}
                  disabled={nutritionistLoading}
                  className="w-full mt-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:from-green-700 hover:to-emerald-700 transition-all duration-300 transform hover:scale-[1.02] disabled:hover:scale-100"
                >
                  {nutritionistLoading ? (
                    <div className="flex items-center justify-center gap-3">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      생성 중...
                    </div>
                  ) : "식단표 생성"}
                </button>
              </div>

              {/* Results */}
              {plan.length > 0 && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-gray-900">생성된 식단표</h3>
                  <div className="flex gap-4 overflow-x-auto pb-4">
                    {plan.map((d) => (
                      <button
                        key={String(d.day)}
                        onClick={() => setDetail(d)}
                        className="min-w-[280px] text-left bg-white border border-gray-200 rounded-2xl p-5 hover:shadow-lg hover:border-green-300 transition-all duration-300 transform hover:scale-105"
                      >
                        <div className="text-sm font-medium text-green-600 mb-2">DAY {d.day}</div>
                        <div className="space-y-1 text-sm">
                          <div className="font-semibold text-gray-900 truncate">🍚 {d.rice}</div>
                          <div className="text-gray-700 truncate">🥣 {d.soup}</div>
                          <div className="text-gray-700 truncate">🥬 {d.side1}</div>
                          <div className="text-gray-700 truncate">🥕 {d.side2}</div>
                          <div className="text-gray-700 truncate">🌶️ {d.side3}</div>
                          <div className="text-blue-600 truncate font-medium">🍎 {d.snack}</div>
                        </div>
                        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-600">
                          <div className="flex justify-between items-center">
                            <span className="font-medium">{d.day_kcal.toFixed(0)} kcal</span>
                            <div className="text-right">
                              <div>C {d.carb_pct_cal.toFixed(0)}% | P {d.prot_pct_cal.toFixed(0)}%</div>
                              <div>F {d.fat_pct_cal.toFixed(0)}%</div>
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal for Plan */}
      {detail && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-[60]">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h4 className="text-xl font-bold text-gray-900">DAY {detail.day} 상세 정보</h4>
              <button 
                onClick={() => setDetail(null)}
                className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors flex items-center justify-center"
              >
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100">
                <h5 className="font-semibold text-gray-900 mb-3">메뉴 구성</h5>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🍚</span>
                    <span className="font-medium">밥:</span>
                    <span className="text-gray-700">{detail.rice}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🥣</span>
                    <span className="font-medium">국:</span>
                    <span className="text-gray-700">{detail.soup}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🥬</span>
                    <span className="font-medium">반찬1:</span>
                    <span className="text-gray-700">{detail.side1}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🥕</span>
                    <span className="font-medium">반찬2:</span>
                    <span className="text-gray-700">{detail.side2}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🌶️</span>
                    <span className="font-medium">반찬3:</span>
                    <span className="text-gray-700">{detail.side3}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🍎</span>
                    <span className="font-medium">간식:</span>
                    <span className="text-blue-600 font-medium">{detail.snack}</span>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-4 border border-blue-100">
                <h5 className="font-semibold text-gray-900 mb-3">영양 정보</h5>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white rounded-lg p-3 text-center border">
                    <div className="text-2xl font-bold text-blue-600">{detail.day_kcal.toFixed(0)}</div>
                    <div className="text-xs text-gray-500">칼로리 (kcal)</div>
                  </div>
                  <div className="bg-white rounded-lg p-3 text-center border">
                    <div className="text-lg font-bold text-green-600">{detail.carb_pct_cal.toFixed(1)}%</div>
                    <div className="text-xs text-gray-500">탄수화물</div>
                  </div>
                  <div className="bg-white rounded-lg p-3 text-center border">
                    <div className="text-lg font-bold text-orange-600">{detail.prot_pct_cal.toFixed(1)}%</div>
                    <div className="text-xs text-gray-500">단백질</div>
                  </div>
                  <div className="bg-white rounded-lg p-3 text-center border">
                    <div className="text-lg font-bold text-red-600">{detail.fat_pct_cal.toFixed(1)}%</div>
                    <div className="text-xs text-gray-500">지방</div>
                  </div>
                </div>
              </div>
            </div>

            <button
              onClick={() => setDetail(null)}
              className="w-full mt-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl font-medium hover:from-green-700 hover:to-emerald-700 transition-all"
            >
              확인
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Auth Form Component
function AuthForm({ mode, onLogin, onSignup, onClose }: {
  mode: AuthMode;
  onLogin: (email: string, password: string) => void;
  onSignup: (name: string, email: string, password: string) => void;
  onClose: () => void;
}) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: ""
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (mode === "login") {
      if (!formData.email || !formData.password) {
        alert("모든 필드를 입력해주세요.");
        return;
      }
      onLogin(formData.email, formData.password);
    } else {
      if (!formData.name || !formData.email || !formData.password || !formData.confirmPassword) {
        alert("모든 필드를 입력해주세요.");
        return;
      }
      if (formData.password !== formData.confirmPassword) {
        alert("비밀번호가 일치하지 않습니다.");
        return;
      }
      onSignup(formData.name, formData.email, formData.password);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {mode === "signup" && (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">이름</label>
          <input
            type="text"
            className="w-full rounded-xl border border-gray-200 px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            placeholder="이름을 입력하세요"
          />
        </div>
      )}

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">이메일</label>
        <input
          type="email"
          className="w-full rounded-xl border border-gray-200 px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          placeholder="이메일을 입력하세요"
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">비밀번호</label>
        <input
          type="password"
          className="w-full rounded-xl border border-gray-200 px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          placeholder="비밀번호를 입력하세요"
        />
      </div>

      {mode === "signup" && (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">비밀번호 확인</label>
          <input
            type="password"
            className="w-full rounded-xl border border-gray-200 px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            value={formData.confirmPassword}
            onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
            placeholder="비밀번호를 다시 입력하세요"
          />
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onClose}
          className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-all"
        >
          취소
        </button>
        <button
          type="submit"
          className="flex-1 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 transition-all"
        >
          {mode === "login" ? "로그인" : "회원가입"}
        </button>
      </div>
    </form>
  );
}